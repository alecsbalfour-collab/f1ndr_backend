# scrapers/module.py

import asyncio

from scrapers.autotrader_scraper import run as run_autotrader
from scrapers.craigslist_scraper import run as run_craigslist
from scrapers.ebay_scraper import run as run_ebay
from scrapers.facebook_scraper import run as run_facebook
from scrapers.kijiji_scraper import run as run_kijiji
from scrapers.marketplace_scraper import run as run_marketplace
from scrapers.realtor_scraper import run as run_realtor
from scrapers.rentals_scraper import run as run_rentals
from scrapers.rentfaster_scraper import run as run_rentfaster
from scrapers.used_scraper import run as run_used
from scrapers.usedca_scraper import run as run_usedca
from scrapers.zillow_scraper import run as run_zillow
from scrapers.neighbourhood_scraper import run as run_neighbourhood


SCRAPERS = {
    "autotrader": run_autotrader,
    "craigslist": run_craigslist,
    "ebay": run_ebay,
    "facebook": run_facebook,
    "kijiji": run_kijiji,
    "marketplace": run_marketplace,
    "rentals": run_rentals,
    "rentfaster": run_rentfaster,
    "used": run_used,
    "usedca": run_usedca,
    "realtor": run_realtor,
    "zillow": run_zillow,
    "neighbourhood": run_neighbourhood,
}

# All scrapers are now async, so ASYNC_SCRAPERS is the same as SCRAPERS
ASYNC_SCRAPERS = SCRAPERS


async def run_all(query: str):
    tasks = []

    for name, scraper in ASYNC_SCRAPERS.items():
        tasks.append(_run_single(name, scraper, query))

    results = await asyncio.gather(*tasks)

    return {
        "query": query,
        "results": {r["platform"]: r for r in results},
    }


async def _run_single(name: str, scraper_func, query: str):
    try:
        result = await scraper_func(query)
        # Handle different result formats from scrapers
        if "success" in result:
            # Used.ca format
            return {
                "platform": name,
                "success": result.get("success", False),
                "listings": result.get("listings", []),
                "error": result.get("error"),
            }
        else:
            # Standard format
            return {
                "platform": name,
                "success": True,
                "listings": result.get("results", []),
                "error": result.get("error"),
            }
    except Exception as e:
        return {
            "platform": name,
            "success": False,
            "listings": [],
            "error": str(e),
        }
