"""
Zillow scraper (Calgary listings by default; the query is any Zillow location search).
"""

from typing import Any, Dict, Optional

from scrapers.base_scraper import BaseScraper


class ZillowScraper(BaseScraper):
    source_name = "zillow"
    base_url = "https://www.zillow.com/calgary-ab/"
    search_url = "https://www.zillow.com/homes/{query}_rb/"
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
