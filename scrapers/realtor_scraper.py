"""
Realtor.ca residential listings scraper.
The query is a city slug in Alberta (e.g. "calgary", "red deer"), defaulting to Calgary.
"""

from typing import Any, Dict, Optional

from scrapers.base_scraper import BaseScraper


class RealtorScraper(BaseScraper):
    source_name = "realtor"
    default_category = "real_estate"
    base_url = "https://www.realtor.ca/ab/calgary/real-estate"
    search_url = "https://www.realtor.ca/ab/{query}/real-estate"
    card_selector = "div.cardCon, [data-testid='listing-card']"
    link_selector = "a.blockLink, a.listingDetailsLink, a[href*='/real-estate/']"
    fields = {
        "title": ".smallListingCardAddress, .listingCardAddress",
        "price": ".smallListingCardPrice, .listingCardPrice",
        "details": ".smallListingCardIconCon, .listingCardIconCon",
    }
    slug_query = True


async def run(query: Optional[str] = None) -> Dict[str, Any]:
    return await RealtorScraper().run(query)
