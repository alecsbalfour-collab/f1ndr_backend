from .module import run_all

from .autotrader_scraper import run as run_autotrader
from .craigslist_scraper import run as run_craigslist
from .ebay_scraper import run as run_ebay
from .facebook_scraper import run as run_facebook
from .kijiji_scraper import run as run_kijiji
from .marketplace_scraper import run as run_marketplace
from .neighbourhood_scraper import run as run_neighbourhood
from .realtor_scraper import run as run_realtor, scrape_realtor
from .rentals_scraper import run as run_rentals
from .rentfaster_scraper import run as run_rentfaster
from .used_scraper import run as run_used
from .usedca_scraper import run as run_usedca
from .zillow_scraper import run as run_zillow

# Convenience exports
scrape_autotrader = run_autotrader
scrape_craigslist = run_craigslist
scrape_ebay = run_ebay
scrape_facebook = run_facebook
scrape_kijiji = run_kijiji
scrape_marketplace = run_marketplace
scrape_neighbourhood = run_neighbourhood
scrape_rentals = run_rentals
scrape_rentfaster = run_rentfaster
scrape_used = run_used
scrape_usedca = run_usedca
scrape_zillow = run_zillow

__all__ = [
    # module.py
    "run_all",

    # scrapers/
    "run_autotrader",
    "run_craigslist",
    "run_ebay",
    "run_facebook",
    "run_kijiji",
    "run_marketplace",
    "run_neighbourhood",
    "run_realtor",
    "scrape_realtor",
    "run_rentals",
    "run_rentfaster",
    "run_used",
    "run_usedca",
    "run_zillow",
    
    # convenience exports
    "scrape_autotrader",
    "scrape_craigslist",
    "scrape_ebay",
    "scrape_facebook",
    "scrape_kijiji",
    "scrape_marketplace",
    "scrape_neighbourhood",
    "scrape_rentals",
    "scrape_rentfaster",
    "scrape_used",
    "scrape_usedca",
    "scrape_zillow",
]
