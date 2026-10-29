"""
Neighbourhood classifieds scraper: city-specific Used.ca network sites.
The region picks the site (regions_config _USED_CITIES); a city-name query is
still accepted for backward compatibility via query_is_city.
"""

from typing import Any, Dict, Optional

from scrapers.used_scraper import UsedNetworkScraper


class NeighbourhoodScraper(UsedNetworkScraper):
    source_name = "neighbourhood_classifieds"
    base_url = "https://www.{host}/classifieds/cars"
    query_is_city = True


async def run(query: Optional[str] = None) -> Dict[str, Any]:
    return await NeighbourhoodScraper().run(query)
