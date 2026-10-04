"""
Playwright base scraper shared by every platform scraper.

Subclasses declare where to go and what to extract:
    source_name, base_url, search_url, card_selector, fields, link_selector
and override build_url / parse_card only when a platform needs custom logic.

Every run() returns the same dict shape and never raises:
    {source, query, url, success, results, count, error, cached, duration_ms, scraped_at}
"""

import asyncio
import logging
import random
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import quote, quote_plus, urljoin

from bs4 import BeautifulSoup, Tag
from playwright.async_api import async_playwright

from f1ndr.db.db import save_scraped_listings
from scrapers.config.settings_config import ScraperConfig
from scrapers.core.metrics_core import metrics_registry
from scrapers.core.normalization_core import parse_price
from scrapers.core.resilience_core import CircuitOpenError, breaker_registry
from scrapers.db.cache_db import cache_get, cache_set

logger = logging.getLogger(__name__)

MAX_QUERY_LENGTH = 200


class ScrapeError(RuntimeError):
    """Raised when a page could not be loaded after all retries."""


def sanitize_query(query: Optional[str]) -> Optional[str]:
    """Collapse whitespace and cap length; reject non-string input."""
    if query is None:
        return None
    if not isinstance(query, str):
        raise ValueError("query must be a string")
    cleaned = " ".join(query.split())[:MAX_QUERY_LENGTH]
    return cleaned or None


class BaseScraper:
    source_name: str = "base"
    base_url: str = ""
    search_url: str = ""
    card_selector: str = ""
    wait_selector: Optional[str] = None
    link_selector: str = "a[href]"
    fields: Dict[str, str] = {}
    slug_query: bool = False
    # Corpus metadata stamped on persisted listings. Region is the market the
    # scraper targets; URLs are Calgary-baked today (multi-region is a roadmap item).
    region: str = "calgary"
    default_category: str = "other"

    def __init__(self, config: Optional[ScraperConfig] = None):
        self.config = config or ScraperConfig.from_env()
        self.breaker = breaker_registry.get(
            self.source_name,
            self.config.breaker_failure_threshold,
            self.config.breaker_reset_seconds,
        )
        self.metrics = metrics_registry.get(self.source_name)

    def build_url(self, query: Optional[str]) -> str:
        """Search URL for `query`, or the default browse page when there is none.
        Platforms that take the query as a path segment set slug_query=True."""
        if not (query and self.search_url):
            return self.base_url
        encoded = quote(query.lower().replace(" ", "-")) if self.slug_query else quote_plus(query)
        return self.search_url.format(query=encoded)

    def absolute_url(self, href: Optional[str]) -> Optional[str]:
        return urljoin(self.base_url, href) if href else None

    @staticmethod
    def text(node: Tag, selector: str) -> Optional[str]:
        element = node.select_one(selector)
        return (element.get_text(" ", strip=True) or None) if element else None

    def parse_card(self, card: Tag) -> Optional[Dict[str, Any]]:
        listing = {name: self.text(card, selector) for name, selector in self.fields.items()}
        link = card if card.name == "a" and card.get("href") else card.select_one(self.link_selector)
        listing["url"] = self.absolute_url(link.get("href")) if link else None
        return listing

    def parse(self, html: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html, "html.parser")
        listings: List[Dict[str, Any]] = []
        seen_urls = set()
        for card in soup.select(self.card_selector):
            try:
                listing = self.parse_card(card)
            except Exception as e:
                logger.warning("%s: skipping unparseable card: %s", self.source_name, e)
                continue
            if not listing or not listing.get("title") or not listing.get("url"):
                continue
            if listing["url"] in seen_urls:
                continue
            seen_urls.add(listing["url"])
            listing["price_value"] = parse_price(listing.get("price"))
            listing["platform"] = self.source_name
            listings.append(listing)
        return listings

    async def fetch_html(self, url: str) -> str:
        """
        Load `url` in headless Chromium and return the rendered HTML.
        Navigation errors are retried with exponential backoff + jitter.
        A missing result selector is not retried: the page loaded, it just has
        no cards (empty search or a block page), so its HTML is returned as-is.
        """
        cfg = self.config
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=cfg.headless)
            try:
                context = await browser.new_context(
                    user_agent=cfg.user_agent,
                    viewport={"width": cfg.viewport_width, "height": cfg.viewport_height},
                    locale=cfg.locale,
                )
                last_error: Optional[Exception] = None
                for attempt in range(cfg.max_retries + 1):
                    page = await context.new_page()
                    try:
                        await page.goto(url, wait_until=cfg.wait_until, timeout=cfg.timeout_ms)
                        try:
                            await page.wait_for_selector(
                                self.wait_selector or self.card_selector,
                                timeout=cfg.selector_timeout_ms,
                            )
                        except Exception:
                            logger.warning("%s: no result cards found at %s", self.source_name, url)
                        return await page.content()
                    except Exception as e:
                        last_error = e
                        logger.warning(
                            "%s: attempt %d/%d failed for %s: %s",
                            self.source_name, attempt + 1, cfg.max_retries + 1, url, e,
                        )
                        if attempt < cfg.max_retries:
                            await asyncio.sleep(
                                cfg.retry_delay * 2 ** attempt + random.uniform(0, cfg.retry_delay)
                            )
                    finally:
                        await page.close()
                raise ScrapeError(f"{self.source_name}: failed to load {url}: {last_error}")
            finally:
                await browser.close()

    def _result(
        self,
        query: Optional[str],
        url: Optional[str],
        started: float,
        listings: Optional[List[Dict[str, Any]]] = None,
        error: Optional[str] = None,
    ) -> Dict[str, Any]:
        listings = listings or []
        return {
            "source": self.source_name,
            "query": query,
            "url": url,
            "success": error is None,
            "results": listings,
            "count": len(listings),
            "error": error,
            "cached": False,
            "duration_ms": round((time.perf_counter() - started) * 1000, 1),
            "scraped_at": datetime.now(timezone.utc).isoformat(),
        }

    async def run(self, query: Optional[str] = None) -> Dict[str, Any]:
        started = time.perf_counter()
        try:
            query = sanitize_query(query)
            url = self.build_url(query)
        except ValueError as e:
            return self._result(None, None, started, error=str(e))

        cache_key = f"{self.source_name}:{url}"
        if self.config.cache_ttl_seconds:
            cached = await cache_get(cache_key)
            if cached is not None:
                self.metrics.record_cache_hit()
                return {**cached, "cached": True}

        try:
            self.breaker.before_call()
        except CircuitOpenError as e:
            self.metrics.record_rejected()
            logger.warning(str(e))
            return self._result(query, url, started, error=str(e))

        try:
            logger.info("%s: scraping %s", self.source_name, url)
            listings = self.parse(await self.fetch_html(url))
        except Exception as e:
            self.breaker.record_failure()
            result = self._result(query, url, started, error=str(e))
            self.metrics.record_failure(result["duration_ms"], str(e))
            logger.error("%s: scrape failed: %s", self.source_name, e)
            return result

        self.breaker.record_success()
        result = self._result(query, url, started, listings=listings)
        self.metrics.record_success(result["duration_ms"], result["count"])
        logger.info("%s: %d listings in %.0fms", self.source_name, result["count"], result["duration_ms"])

        # Persist into the f1ndr corpus, then feed watchr alert matching.
        # Neither must ever fail the scrape itself.
        if listings:
            try:
                saved = await save_scraped_listings(
                    listings,
                    platform=self.source_name,
                    category=self.default_category,
                    region=self.region,
                )
                try:
                    from watchr.core.core import evaluate_listings
                    await evaluate_listings(saved)
                except Exception as e:
                    logger.warning("%s: watchr alert matching failed: %s", self.source_name, e)
            except Exception as e:
                logger.warning("%s: could not persist scraped listings: %s", self.source_name, e)
        if self.config.cache_ttl_seconds:
            await cache_set(cache_key, result, ttl=self.config.cache_ttl_seconds)
        return result
