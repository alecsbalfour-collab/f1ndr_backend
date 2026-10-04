"""
RentFaster.ca Calgary rentals scraper.
"""

from typing import Any, Dict, Optional

from scrapers.base_scraper import BaseScraper


class RentFasterScraper(BaseScraper):
    source_name = "rentfaster"
    default_category = "real_estate"
    base_url = "https://www.rentfaster.ca/ab/calgary/rentals/"
    search_url = "https://www.rentfaster.ca/ab/calgary/rentals/?keywords={query}"
    card_selector = "div.listing-item, li.listing-item, div.listing"
    link_selector = "a.listing-link, a[href*='/ab/calgary/rentals/']"
    fields = {
        "title": ".listing-title, .address, h3",
        "price": ".listing-price, .price",
        "details": ".listing-details, .bedrooms",
        "location": ".listing-community, .location",
    }


async def run(query: Optional[str] = None) -> Dict[str, Any]:
    return await RentFasterScraper().run(query)
