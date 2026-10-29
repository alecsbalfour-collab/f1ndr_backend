"""
Zillow scraper (Calgary listings by default; the query is any Zillow location search).
"""

from typing import Any, Dict, Optional

from scrapers.base_scraper import BaseScraper


class ZillowScraper(BaseScraper):
    source_name = "zillow"
    default_category = "real_estate"
    base_url = "https://www.zillow.com/{cityslug}/"
    search_url = "https://www.zillow.com/{cityslug}/"
    query_is_city = True
    card_selector = "article[data-test='property-card'], li article"
    link_selector = "a[data-test='property-card-link'], a[href*='/homedetails/']"
    fields = {
        "title": "address[data-test='property-card-addr'], address",
        "price": "[data-test='property-card-price']",
        "details": "ul[class*='HomeDetailsList'], [data-test='property-card-details']",
    }
    slug_query = True


async def run(query: Optional[str] = None) -> Dict[str, Any]:
    return await ZillowScraper().run(query)
