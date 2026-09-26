import pytest

from scrapers.base_scraper import BaseScraper, ScrapeError, sanitize_query
from scrapers.config.settings_config import ScraperConfig
from scrapers.core.normalization_core import parse_price
from scrapers.core.resilience_core import CircuitBreaker, CircuitOpenError

HTML = """
<div class="card"><a href="/item/1"><h2>2018 Toyota Corolla</h2></a><span class="price">$15,900</span></div>
<div class="card"><a href="/item/1"><h2>Duplicate</h2></a></div>
<div class="card"><h2>No link</h2></div>
<div class="card"><a href="https://other.example/item/2"><h2>2012 Ford F-150</h2></a><span class="price">Please contact</span></div>
"""


class FakeScraper(BaseScraper):
    source_name = "fake"
    base_url = "https://site.example/browse"
    search_url = "https://site.example/search?q={query}"
    card_selector = "div.card"
    fields = {"title": "h2", "price": ".price"}

    def __init__(self, config=None, pages=None):
        super().__init__(config or ScraperConfig(retry_delay=0))
        self.pages = list(pages or [])
        self.fetches = 0

    async def fetch_html(self, url):
        self.fetches += 1
        page = self.pages.pop(0)
        if isinstance(page, Exception):
            raise page
        return page


def test_scraper_keeps_its_own_source_name():
    assert FakeScraper().source_name == "fake"


def test_parse_normalizes_dedupes_and_skips_incomplete_cards():
    listings = FakeScraper().parse(HTML)
    assert listings == [
        {"title": "2018 Toyota Corolla", "price": "$15,900", "url": "https://site.example/item/1",
         "price_value": 15900.0, "platform": "fake"},
        {"title": "2012 Ford F-150", "price": "Please contact", "url": "https://other.example/item/2",
         "price_value": None, "platform": "fake"},
    ]


def test_build_url_encodes_query_and_defaults_to_browse_page():
    scraper = FakeScraper()
    assert scraper.build_url("honda civic & more") == "https://site.example/search?q=honda+civic+%26+more"
    assert scraper.build_url(None) == "https://site.example/browse"


def test_sanitize_query():
    assert sanitize_query("  honda   civic ") == "honda civic"
    assert sanitize_query("   ") is None
    assert len(sanitize_query("x" * 500)) == 200
    with pytest.raises(ValueError):
        sanitize_query(123)


@pytest.mark.parametrize("raw,expected", [
    ("C $12,500.00", 12500.0), ("$1,200 - $1,500", 1200.0), ("Free", None), (None, None),
])
def test_parse_price(raw, expected):
    assert parse_price(raw) == expected


async def test_run_success_returns_standard_result_and_records_metrics():
    scraper = FakeScraper(pages=[HTML])
    result = await scraper.run("corolla")
    assert result["success"] is True
    assert result["count"] == 2
    assert result["error"] is None
    assert result["url"] == "https://site.example/search?q=corolla"
    assert scraper.metrics.successes == 1
    assert scraper.metrics.last_listing_count == 2


async def test_run_serves_repeat_queries_from_cache():
    scraper = FakeScraper(pages=[HTML])
    await scraper.run("corolla")
    cached = await scraper.run("corolla")
    assert cached["cached"] is True
    assert scraper.fetches == 1
    assert scraper.metrics.cache_hits == 1


async def test_run_failure_never_raises_and_opens_circuit():
    config = ScraperConfig(retry_delay=0, cache_ttl_seconds=0, breaker_failure_threshold=2)
    scraper = FakeScraper(config, pages=[ScrapeError("boom"), ScrapeError("boom")])
    for _ in range(2):
        result = await scraper.run("x")
        assert result == {**result, "success": False, "error": "boom", "count": 0}
    rejected = await scraper.run("x")
    assert "Circuit open" in rejected["error"]
    assert scraper.fetches == 2
    assert scraper.metrics.failures == 2
    assert scraper.metrics.rejected == 1


async def test_run_rejects_invalid_query_without_fetching():
    scraper = FakeScraper()
    result = await scraper.run(["not", "a", "string"])
    assert result["success"] is False
    assert scraper.fetches == 0


def test_circuit_breaker_half_open_cycle():
    now = [0.0]
    breaker = CircuitBreaker("x", failure_threshold=2, reset_seconds=10, clock=lambda: now[0])
    breaker.record_failure()
    assert breaker.state == "closed"
    breaker.record_failure()
    assert breaker.state == "open"
    with pytest.raises(CircuitOpenError):
        breaker.before_call()
    now[0] = 10
    assert breaker.state == "half_open"
    breaker.before_call()
    breaker.record_failure()
    assert breaker.state == "open"
    now[0] = 20
    breaker.record_success()
    assert breaker.state == "closed"


def test_config_reads_env_overrides(monkeypatch):
    monkeypatch.setenv("f1ndr_SCRAPER_MAX_RETRIES", "5")
    monkeypatch.setenv("f1ndr_SCRAPER_HEADLESS", "false")
    monkeypatch.setenv("f1ndr_SCRAPER_RETRY_DELAY", "0.5")
    config = ScraperConfig.from_env()
    assert (config.max_retries, config.headless, config.retry_delay) == (5, False, 0.5)


class _FakePage:
    def __init__(self, browser):
        self.browser = browser

    async def goto(self, url, **_):
        self.browser.gotos += 1
        if self.browser.gotos <= self.browser.fail_first:
            raise TimeoutError("navigation timeout")

    async def wait_for_selector(self, *_args, **_kwargs):
        raise TimeoutError("no cards")

    async def content(self):
        return "<html>ok</html>"

    async def close(self):
        pass


class _FakeBrowser:
    def __init__(self, fail_first):
        self.fail_first = fail_first
        self.gotos = 0
        self.closed = False

    async def new_context(self, **_):
        return self

    async def new_page(self):
        return _FakePage(self)

    async def close(self):
        self.closed = True


def _patch_playwright(monkeypatch, browser):
    class _Chromium:
        async def launch(self, **_):
            return browser

    class _Playwright:
        chromium = _Chromium()

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

    monkeypatch.setattr("scrapers.base_scraper.async_playwright", _Playwright)


async def test_fetch_html_retries_navigation_errors_then_succeeds(monkeypatch):
    browser = _FakeBrowser(fail_first=2)
    _patch_playwright(monkeypatch, browser)
    html = await BaseScraper.fetch_html(FakeScraper(ScraperConfig(max_retries=2, retry_delay=0)), "https://x")
    assert html == "<html>ok</html>"
    assert browser.gotos == 3
    assert browser.closed


async def test_fetch_html_raises_after_exhausting_retries(monkeypatch):
    browser = _FakeBrowser(fail_first=99)
    _patch_playwright(monkeypatch, browser)
    with pytest.raises(ScrapeError):
        await BaseScraper.fetch_html(FakeScraper(ScraperConfig(max_retries=1, retry_delay=0)), "https://x")
    assert browser.gotos == 2
    assert browser.closed
