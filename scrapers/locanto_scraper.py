"""
Locanto Calgary classifieds scraper.
"""

from typing import Any, Dict, Optional

from scrapers.base_scraper import BaseScraper


class LocantoScraper(BaseScraper):
    source_name = "locanto"
    base_url = "https://calgary.locanto.ca/Cars/201/"
    search_url = "https://calgary.locanto.ca/q/?query={query}"
    card_selector = "article.posting_listing, div.resultRow, li.bp_ad"
    link_selector = "a.posting_listing__title, a.bp_ad__link, a[href*='/ID_']"
    fields = {
        "title": ".posting_listing__title, .bp_ad__title, h3",
        "price": ".posting_listing__price, .bp_ad__price, .price",
        "location": ".posting_listing__city, .bp_ad__city, .location",
    }


async def run(query: Optional[str] = None) -> Dict[str, Any]:
    return await LocantoScraper().run(query)
