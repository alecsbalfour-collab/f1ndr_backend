"""
Facebook Marketplace scraper (Calgary, all categories).
Shares card parsing with the vehicles scraper.
"""

from typing import Any, Dict, Optional

from scrapers.facebook_scraper import FacebookMarketplaceScraper


class MarketplaceScraper(FacebookMarketplaceScraper):
    source_name = "marketplace"
    base_url = "https://www.facebook.com/marketplace/calgary/"


async def run(query: Optional[str] = None) -> Dict[str, Any]:
    return await MarketplaceScraper().run(query)
