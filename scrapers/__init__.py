from .module import SCRAPER_CLASSES, health_report, run_all, run_scraper

from .autotrader_scraper import run as run_autotrader
from .craigslist_scraper import run as run_craigslist
from .ebay_scraper import run as run_ebay
from .kijiji_scraper import run as run_kijiji
from .locanto_scraper import run as run_locanto
from .neighbourhood_scraper import run as run_neighbourhood
from .realtor_scraper import run as run_realtor
from .rentals_scraper import run as run_rentals
from .rentfaster_scraper import run as run_rentfaster
from .used_scraper import run as run_used
from .usedca_scraper import run as run_usedca
from .zillow_scraper import run as run_zillow

# Convenience exports
scrape_autotrader = run_autotrader
scrape_craigslist = run_craigslist
scrape_ebay = run_ebay
scrape_kijiji = run_kijiji
scrape_locanto = run_locanto
scrape_neighbourhood = run_neighbourhood
scrape_realtor = run_realtor
scrape_rentals = run_rentals
scrape_rentfaster = run_rentfaster
scrape_used = run_used
scrape_usedca = run_usedca
scrape_zillow = run_zillow

__all__ = [
    # module.py
    "SCRAPER_CLASSES",
    "health_report",
    "run_all",
    "run_scraper",

    # scrapers/
    "run_autotrader",
    "run_craigslist",
    "run_ebay",
    "run_kijiji",
    "run_locanto",
    "run_neighbourhood",
    "run_realtor",
    "run_rentals",
    "run_rentfaster",
    "run_used",
    "run_usedca",
    "run_zillow",

    # convenience exports
    "scrape_autotrader",
    "scrape_craigslist",
    "scrape_ebay",
    "scrape_kijiji",
    "scrape_locanto",
    "scrape_neighbourhood",
    "scrape_realtor",
    "scrape_rentals",
    "scrape_rentfaster",
    "scrape_used",
    "scrape_usedca",
    "scrape_zillow",
]
