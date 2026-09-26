# scrapers/module.py
"""
Scraper registry and orchestration: run one platform, fan out across many with
bounded concurrency, and report per-platform health (circuit state + metrics).
"""

import asyncio
from typing import Any, Dict, Iterable, Optional, Type

from scrapers.autotrader_scraper import AutotraderScraper
from scrapers.base_scraper import BaseScraper
from scrapers.config.settings_config import ScraperConfig
from scrapers.core.metrics_core import metrics_registry
from scrapers.core.resilience_core import breaker_registry
from scrapers.craigslist_scraper import CraigslistScraper
from scrapers.ebay_scraper import EbayScraper
from scrapers.facebook_scraper import FacebookMarketplaceScraper
from scrapers.kijiji_scraper import KijijiScraper
from scrapers.locanto_scraper import LocantoScraper
from scrapers.marketplace_scraper import MarketplaceScraper
from scrapers.neighbourhood_scraper import NeighbourhoodScraper
from scrapers.realtor_scraper import RealtorScraper
from scrapers.rentals_scraper import RentalsScraper
from scrapers.rentfaster_scraper import RentFasterScraper
from scrapers.used_scraper import UsedScraper
from scrapers.usedca_scraper import UsedCAScraper
from scrapers.zillow_scraper import ZillowScraper


SCRAPER_CLASSES: Dict[str, Type[BaseScraper]] = {
    "autotrader": AutotraderScraper,
    "craigslist": CraigslistScraper,
    "ebay": EbayScraper,
    "facebook": FacebookMarketplaceScraper,
    "kijiji": KijijiScraper,
    "locanto": LocantoScraper,
    "marketplace": MarketplaceScraper,
    "neighbourhood": NeighbourhoodScraper,
    "realtor": RealtorScraper,
    "rentals": RentalsScraper,
    "rentfaster": RentFasterScraper,
    "used": UsedScraper,
    "usedca": UsedCAScraper,
    "zillow": ZillowScraper,
}


def _validate_platforms(platforms: Iterable[str]) -> list[str]:
    names = list(platforms)
    unknown = sorted(set(names) - set(SCRAPER_CLASSES))
    if unknown:
        raise ValueError(
            f"Unsupported scraper platform(s): {', '.join(unknown)}. "
            f"Supported: {', '.join(SCRAPER_CLASSES)}"
        )
    return names


async def run_scraper(
    platform: str, query: Optional[str] = None, config: Optional[ScraperConfig] = None
) -> Dict[str, Any]:
    _validate_platforms([platform])
    return await SCRAPER_CLASSES[platform](config).run(query)


async def run_all(
    query: Optional[str] = None,
    platforms: Optional[Iterable[str]] = None,
    config: Optional[ScraperConfig] = None,
) -> Dict[str, Any]:
    """Run the given platforms (default: all), at most `max_concurrency` browsers at once."""
    config = config or ScraperConfig.from_env()
    names = _validate_platforms(platforms or SCRAPER_CLASSES)
    semaphore = asyncio.Semaphore(config.max_concurrency)

    async def _bounded(name: str) -> Dict[str, Any]:
        async with semaphore:
            return await run_scraper(name, query, config)

    results = await asyncio.gather(*(_bounded(name) for name in names))
    return {
        "query": query,
        "platforms": names,
        "total": sum(result["count"] for result in results),
        "failed": [name for name, result in zip(names, results) if not result["success"]],
        "results": dict(zip(names, results)),
    }


def health_report() -> Dict[str, Any]:
    """Circuit state and run metrics per platform. Status is ok / degraded / down."""
    breakers = breaker_registry.snapshot()
    metrics = metrics_registry.snapshot()
    platforms = {
        name: {
            "source": cls.source_name,
            "circuit": breakers.get(cls.source_name, {"state": "closed"}),
            "metrics": metrics.get(cls.source_name),
        }
        for name, cls in SCRAPER_CLASSES.items()
    }
    open_count = sum(p["circuit"]["state"] == "open" for p in platforms.values())
    status = "ok" if open_count == 0 else "down" if open_count == len(platforms) else "degraded"
    return {"status": status, "open_circuits": open_count, "platforms": platforms}
