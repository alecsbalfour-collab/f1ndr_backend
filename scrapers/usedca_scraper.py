"""
UsedCalgary.com vehicle scraper.
"""

from typing import Any, Dict, Optional

from scrapers.used_scraper import UsedNetworkScraper


class UsedCAScraper(UsedNetworkScraper):
    source_name = "usedca"
    base_url = "https://www.usedcalgary.com/classifieds/cars"
    search_url = "https://www.usedcalgary.com/classifieds/cars?keywords={query}"


async def run(query: Optional[str] = None) -> Dict[str, Any]:
    return await UsedCAScraper().run(query)
