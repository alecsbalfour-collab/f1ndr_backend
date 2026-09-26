"""
AutoTrader.ca vehicle scraper (Calgary, 100 km radius).
"""

from typing import Any, Dict, Optional

from scrapers.base_scraper import BaseScraper

_SEARCH = "https://www.autotrader.ca/cars/ab/calgary/?rcp=100&srt=35&prx=100&prv=Alberta&loc=Calgary%2C%20AB"


class AutotraderScraper(BaseScraper):
    source_name = "autotrader"
    base_url = _SEARCH
    search_url = _SEARCH + "&kwd={query}"
    card_selector = "div.result-item, [data-testid='search-listing-card']"
    link_selector = "a.inner-link, a.result-title, a[href*='/a/']"
    fields = {
        "title": ".title-with-trim, .result-title, h2",
        "price": ".price-amount, [data-testid='price']",
        "location": ".proximity-text, .result-location",
        "mileage": ".odometer-proximity, .kms",
    }


async def run(query: Optional[str] = None) -> Dict[str, Any]:
    return await AutotraderScraper().run(query)
