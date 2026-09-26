"""
Kijiji Calgary scraper. Browses cars & trucks by default; keyword searches cover all categories.
"""

from typing import Any, Dict, Optional

from scrapers.base_scraper import BaseScraper


class KijijiScraper(BaseScraper):
    source_name = "kijiji"
    base_url = "https://www.kijiji.ca/b-cars-trucks/calgary/c174l1700199"
    search_url = "https://www.kijiji.ca/b-calgary/{query}/k0l1700199"
    card_selector = "[data-testid='listing-card'], div.search-item"
    link_selector = "a[data-testid='listing-link'], a.title, a[href*='/v-']"
    fields = {
        "title": "[data-testid='listing-title'], .title",
        "price": "[data-testid='listing-price'], .price",
        "location": "[data-testid='listing-location'], .location",
        "posted": "[data-testid='listing-date'], .date-posted",
    }
    slug_query = True


async def run(query: Optional[str] = None) -> Dict[str, Any]:
    return await KijijiScraper().run(query)
