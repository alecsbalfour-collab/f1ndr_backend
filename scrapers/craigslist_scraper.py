"""
Craigslist Calgary for-sale scraper.
"""

from typing import Any, Dict, Optional

from scrapers.base_scraper import BaseScraper


class CraigslistScraper(BaseScraper):
    source_name = "craigslist"
    base_url = "https://calgary.craigslist.org/search/sss"
    search_url = "https://calgary.craigslist.org/search/sss?query={query}"
    card_selector = "li.cl-static-search-result, li.cl-search-result, li.result-row"
    fields = {
        "title": ".title, .label, .result-title",
        "price": ".price, .priceinfo, .result-price",
        "location": ".location, .result-hood",
    }


async def run(query: Optional[str] = None) -> Dict[str, Any]:
    return await CraigslistScraper().run(query)
