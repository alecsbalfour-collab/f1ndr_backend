"""
Playwright base scraper shared by every platform scraper.

Subclasses declare where to go and what to extract:
    source_name, base_url, search_url, card_selector, fields, link_selector
and override build_url / parse_card only when a platform needs custom logic.

Every run() returns the same dict shape and never raises:
    {source, query, url, success, results, count, error, cached, duration_ms, scraped_at}
"""

import asyncio
import html
import logging
import random
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import quote, quote_plus, urljoin

from bs4 import BeautifulSoup, Tag
from playwright.async_api import async_playwright

from f1ndr.db.db import save_scraped_listings
from scrapers.config.regions_config import DEFAULT_REGION, REGIONS, get_region_info, normalize_region
from scrapers.config.settings_config import ScraperConfig
from scrapers.core.metrics_core import metrics_registry
from scrapers.core.normalization_core import parse_price
from scrapers.core.resilience_core import CircuitOpenError, breaker_registry
from scrapers.db.cache_db import cache_get, cache_set

logger = logging.getLogger(__name__)

MAX_QUERY_LENGTH = 200

# URL-path hints for multi-vertical sites whose cards carry no category field.
# Checked against the listing URL and the page being scraped (browse URLs count).
_URL_CATEGORY_HINTS = (
    ("/v-cars-trucks/", "vehicles"),
    ("/v-autos-other/", "vehicles"),
    ("/b-cars-trucks/", "vehicles"),
    ("/cto/", "vehicles"),
    ("/ctd/", "vehicles"),
    ("/v-apartments-condos-for-rent/", "real_estate"),
    ("/v-real-estate/", "real_estate"),
    ("/apa/", "real_estate"),
    ("/rea/", "real_estate"),
    # RV ads are vehicles on this platform family.
    ("/v-rv-", "vehicles"),
    ("/v-travel-trailer", "vehicles"),
    ("/v-motorhome", "vehicles"),
    ("/rvs/", "vehicles"),
    ("rvtrader.com", "vehicles"),
)

# Subcategory inference from listing URL/title — RV kinds only for now.
_SUBCATEGORY_HINTS = (
    (("fifth wheel", "fifth-wheel", "/v-fifth-wheel", "5th wheel"), "fifth_wheel"),
    (("travel trailer", "travel-trailer", "/v-travel-trailer"), "travel_trailer"),
    (("toy hauler", "toy-hauler", "/v-toy-hauler"), "toy_hauler"),
    (("truck camper", "truck-camper", "/v-truck-camper"), "truck_camper"),
    (("class a", "class-a", "diesel pusher"), "motorhome_a"),
    (("class b", "class-b", "camper van", "campervan"), "motorhome_b"),
    (("class c", "class-c"), "motorhome_c"),
    (("motorcycle", "/v-motorcycles"), "motorcycle"),
    (("sedan", "/v-cars-trucks"), "car"),
)


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
    # Corpus metadata stamped on persisted listings. `region` is the market the
    # scraper targets; URLs are built from regions_config templates.
    region: str = DEFAULT_REGION
    default_category: str = "other"
    # City-scraped sites (realtor/rentals/zillow/neighbourhood): a query that is a
    # region name is treated as the target region for backward compatibility.
    query_is_city: bool = False

    def __init__(self, config: Optional[ScraperConfig] = None, region: Optional[str] = None):
        self.config = config or ScraperConfig.from_env()
        self._active_region = region or self.region
        self.breaker = breaker_registry.get(
            self.source_name,
            self.config.breaker_failure_threshold,
            self.config.breaker_reset_seconds,
        )
        self.metrics = metrics_registry.get(self.source_name)

    def region_params(self) -> Dict[str, str]:
        """URL template kwargs for the active region from the platform map."""
        info = get_region_info(self._active_region)
        return info["platforms"].get(self.source_name) or {}

    def build_url(self, query: Optional[str]) -> str:
        """Search URL for `query`, or the default browse page when there is none.
        Platforms that take the query as a path segment set slug_query=True."""
        params = self.region_params()
        if not (query and self.search_url):
            return self.base_url.format(**params)
        encoded = quote(query.lower().replace(" ", "-")) if self.slug_query else quote_plus(query)
        return self.search_url.format(query=encoded, **params)

    def absolute_url(self, href: Optional[str]) -> Optional[str]:
        return urljoin(self.base_url, href) if href else None

    @staticmethod
    def text(node: Tag, selector: str) -> Optional[str]:
        element = node.select_one(selector)
        if not element:
            return None
        # Double-unescape: platforms ship doubly-encoded entities (e.g. &amp;#x27;).
        return html.unescape(html.unescape(element.get_text(" ", strip=True))) or None

    def parse_card(self, card: Tag) -> Optional[Dict[str, Any]]:
        listing = {name: self.text(card, selector) for name, selector in self.fields.items()}
        link = card if card.name == "a" and card.get("href") else card.select_one(self.link_selector)
        listing["url"] = self.absolute_url(link.get("href")) if link else None
        if not listing.get("image"):
            img = card.select_one("img[src], img[data-src]")
            if img:
                listing["image"] = self.absolute_url(img.get("src") or img.get("data-src"))
        return listing

    def classify_listing(self, listing: Dict[str, Any], query: Optional[str] = None) -> str:
        """Infer a listing's category from URL-path hints (the listing's own URL
        and the page being scraped); falls back to the scraper's default_category."""
        blob = " ".join(p for p in (listing.get("url"), self.build_url(query)) if p)
        for pattern, category in _URL_CATEGORY_HINTS:
            if pattern in blob:
                return category
        return self.default_category

    def infer_subcategory(self, listing: Dict[str, Any]) -> Optional[str]:
        """Guess a vehicle subcategory from the listing's URL + title."""
        blob = f"{listing.get('url') or ''} {listing.get('title') or ''}".lower()
        for keywords, subcategory in _SUBCATEGORY_HINTS:
            if any(k in blob for k in keywords):
                return subcategory
        return None

    def parse(self, html: str, query: Optional[str] = None) -> List[Dict[str, Any]]:
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
            listing["category"] = self.classify_listing(listing, query)
            if not listing.get("subcategory"):
                sub = self.infer_subcategory(listing)
                if sub:
                    listing["subcategory"] = sub
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
            browser = await playwright.chromium.launch(
                headless=cfg.headless,
                # Container runtime: no user namespaces, tiny /dev/shm, ~512MB RAM.
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-extensions",
                    "--disable-background-networking",
                    "--no-zygote",
                    "--js-flags=--max-old-space-size=256",
                ],
            )
            try:
                context = await browser.new_context(
                    user_agent=cfg.user_agent,
                    viewport={"width": cfg.viewport_width, "height": cfg.viewport_height},
                    locale=cfg.locale,
                )
                # Scraping only needs the DOM: images/fonts/media cost the most
                # memory and are never used by the parser. Abort them at the
                # network layer; img src attributes still appear in the HTML.
                await context.route(
                    "**/*",
                    lambda route: (
                        route.abort()
                        if route.request.resource_type in {"image", "media", "font"}
                        else route.continue_()
                    ),
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
        region: Optional[str] = None,
    ) -> Dict[str, Any]:
        listings = listings or []
        return {
            "source": self.source_name,
            "query": query,
            "region": region or self._active_region,
            "url": url,
            "success": error is None,
            "results": listings,
            "count": len(listings),
            "error": error,
            "cached": False,
            "duration_ms": round((time.perf_counter() - started) * 1000, 1),
            "scraped_at": datetime.now(timezone.utc).isoformat(),
        }

    async def run(self, query: Optional[str] = None, region: Optional[str] = None) -> Dict[str, Any]:
        started = time.perf_counter()
        # Backward compat: on city-scraped sites a city-name query is the region.
        if region is None and self.query_is_city and query:
            try:
                region = normalize_region(query)
                query = None
            except ValueError:
                pass
        try:
            active_region = normalize_region(region or self._active_region)
            if self.source_name not in get_region_info(active_region)["platforms"]:
                raise ValueError(f"{self.source_name} is not available in region '{active_region}'")
            self._active_region = active_region
            query = sanitize_query(query)
            url = self.build_url(query)
        except ValueError as e:
            return self._result(query, None, started, error=str(e), region=region)

        cache_key = f"{self.source_name}:{active_region}:{url}"
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
            listings = self.parse(await self.fetch_html(url), query)
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
                    region=active_region,
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
