"""
Used.ca network scrapers (used.ca, usedcalgary.com, usededmonton.com share one markup).
`UsedNetworkScraper` holds the shared selectors; the used / usedca / neighbourhood
scrapers only differ in which site and URL they target.
"""

from typing import Any, Dict, Optional

from scrapers.base_scraper import BaseScraper


class UsedNetworkScraper(BaseScraper):
    card_selector = "div.listing, li.listing, article.listing-card, div.ad-item"
    link_selector = "a.listing-title, a.title, a[href*='/classifieds/']"
    fields = {
        "title": ".listing-title, .title, h2, h3",
        "price": ".price, .listing-price",
        "location": ".location, .listing-location",
        "posted": ".date, .listing-date, time",
    }


class UsedScraper(UsedNetworkScraper):
    source_name = "used"
    base_url = "https://www.used.ca/classifieds/all"
    search_url = "https://www.used.ca/classifieds/all?keywords={query}"


async def run(query: Optional[str] = None) -> Dict[str, Any]:
    return await UsedScraper().run(query)
