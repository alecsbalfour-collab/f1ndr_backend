"""
RVTrader.com scraper — North America RV marketplace (travel trailers, fifth
wheels, motorhomes, truck campers). Region-agnostic: one site, all regions.
"""

from typing import Any, Dict, Optional

from scrapers.base_scraper import BaseScraper


class RVTraderScraper(BaseScraper):
    source_name = "rvtrader"
    default_category = "vehicles"
    base_url = "https://www.rvtrader.com/rvs-for-sale?condition=used"
    search_url = "https://www.rvtrader.com/rvs-for-sale?condition=used&keyword={query}"
    card_selector = "div.listing-card, li.listing-card, div.rv-listing, article"
    link_selector = "a[href*='/listing/'], a.listing-card__title, h3 a"
    fields = {
        "title": ".listing-card__title, .title, h2, h3",
        "price": ".listing-card__price, .price, [data-testid='price']",
        "location": ".listing-card__location, .location, .dealer-location",
        "posted": ".listing-card__date, .date-listed, time",
    }


async def run(query: Optional[str] = None) -> Dict[str, Any]:
    return await RVTraderScraper().run(query)
