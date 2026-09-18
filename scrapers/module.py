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
}


# Async wrappers for sync scrapers
async def run_autotrader_async(query: str):
    return run_autotrader(query)

async def run_craigslist_async(query: str):
    return run_craigslist(query)

async def run_ebay_async(query: str):
    return run_ebay(query)

async def run_facebook_async(query: str):
    return run_facebook(query)

async def run_kijiji_async(query: str):
    return run_kijiji(query)

async def run_marketplace_async(query: str):
    return run_marketplace(query)

async def run_realtor_async(query: str):
    return run_realtor(query)

async def run_rentals_async(query: str):
    return run_rentals(query)

async def run_rentfaster_async(query: str):
    return run_rentfaster(query)

async def run_used_async(query: str):
    return run_used(query)

async def run_usedca_async(query: str):
    return run_usedca(query)

async def run_zillow_async(query: str):
    return run_zillow(query)


ASYNC_SCRAPERS = {
    "autotrader": run_autotrader_async,
    "craigslist": run_craigslist_async,
    "ebay": run_ebay_async,
    "facebook": run_facebook_async,
    "kijiji": run_kijiji_async,
    "marketplace": run_marketplace_async,
    "rentals": run_rentals_async,
    "rentfaster": run_rentfaster_async,
    "used": run_used_async,
    "usedca": run_usedca_async,
    "realtor": run_realtor_async,
    "zillow": run_zillow_async,
}


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
        return {
            "platform": name,
            "success": True,
            "listings": result.get("results", []),
            "error": None,
        }
    except Exception as e:
        return {
            "platform": name,
            "success": False,
            "listings": [],
            "error": str(e),
        }
