"""
Rentals.ca scraper. The query is a city slug (e.g. "calgary", "edmonton"), defaulting to Calgary.
"""

from typing import Any, Dict, Optional

from scrapers.base_scraper import BaseScraper


class RentalsScraper(BaseScraper):
    source_name = "rentals_ca"
    base_url = "https://rentals.ca/calgary"
    search_url = "https://rentals.ca/{query}"
    card_selector = "div.listing-card, article.listing-card"
    link_selector = "a.listing-card__details-link, a[href*='rentals.ca/'], a[href^='/']"
    fields = {
        "title": ".listing-card__title, .listing-card__address, .address",
        "price": ".listing-card__price, .price",
        "details": ".listing-card__main-features, .listing-card__details, .bedrooms",
    }
    slug_query = True


async def run(query: Optional[str] = None) -> Dict[str, Any]:
    return await RentalsScraper().run(query)
