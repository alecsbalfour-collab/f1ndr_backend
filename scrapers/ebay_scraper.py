"""
eBay.ca search scraper. Supports both the legacy `s-item` and current `s-card` result markup.
"""

from typing import Any, Dict, Optional

from bs4 import Tag

from scrapers.base_scraper import BaseScraper


class EbayScraper(BaseScraper):
    source_name = "ebay"
    base_url = "https://www.ebay.ca/sch/i.html?_nkw=vehicles&_sacat=0"
    search_url = "https://www.ebay.ca/sch/i.html?_nkw={query}&_sacat=0"
    card_selector = "li.s-item, li.s-card"
    link_selector = "a.s-item__link, a.su-link, a[href*='/itm/']"
    fields = {
        "title": ".s-item__title, .s-card__title",
        "price": ".s-item__price, .s-card__price",
        "location": ".s-item__location, .s-item__itemLocation",
        "condition": ".SECONDARY_INFO, .s-card__subtitle",
    }

    def parse_card(self, card: Tag) -> Optional[Dict[str, Any]]:
        listing = super().parse_card(card)
        title = listing.get("title") or ""
        if title.lower().startswith("shop on ebay"):
            return None
        listing["title"] = title.removeprefix("New Listing").strip() or None
        if listing["url"]:
            listing["url"] = listing["url"].split("?")[0]
        return listing


async def run(query: Optional[str] = None) -> Dict[str, Any]:
    return await EbayScraper().run(query)
