"""
Neighbourhood classifieds scraper: city-specific Used.ca network sites.
The query is the city name ("calgary" or "edmonton"), defaulting to Calgary.
"""

from typing import Any, Dict, Optional

from scrapers.used_scraper import UsedNetworkScraper

CITY_URLS = {
    "calgary": "https://www.usedcalgary.com/classifieds/cars",
    "edmonton": "https://www.usededmonton.com/classifieds/cars",
}


class NeighbourhoodScraper(UsedNetworkScraper):
    source_name = "neighbourhood_classifieds"
    base_url = CITY_URLS["calgary"]

    def build_url(self, query: Optional[str]) -> str:
        city = (query or "calgary").lower()
        if city not in CITY_URLS:
            raise ValueError(f"Unsupported city: {query}. Supported: {', '.join(CITY_URLS)}")
        return CITY_URLS[city]


async def run(query: Optional[str] = None) -> Dict[str, Any]:
    return await NeighbourhoodScraper().run(query)
