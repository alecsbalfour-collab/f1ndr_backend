"""
Facebook Marketplace scraper (Calgary vehicles).

Marketplace cards are anchors to /marketplace/item/<id>/ whose text spans are
ordered price, title, location, mileage. Facebook frequently serves a login wall
to logged-out browsers; in that case zero listings are returned.
"""

from typing import Any, Dict, Optional

from bs4 import Tag

from scrapers.base_scraper import BaseScraper


class FacebookMarketplaceScraper(BaseScraper):
    source_name = "facebook_marketplace"
    base_url = "https://www.facebook.com/marketplace/calgary/vehicles"
    search_url = "https://www.facebook.com/marketplace/calgary/search?query={query}"
    card_selector = "a[href*='/marketplace/item/']"

    def parse_card(self, card: Tag) -> Optional[Dict[str, Any]]:
        texts = list(dict.fromkeys(
            text for span in card.find_all("span") if (text := span.get_text(strip=True))
        ))
        price = next(
            (t for t in texts if t.startswith(("$", "CA$")) or t.lower() == "free"), None
        )
        details = [t for t in texts if t != price]
        return {
            "title": details[0] if details else None,
            "price": price,
            "location": details[1] if len(details) > 1 else None,
            "mileage": details[2] if len(details) > 2 else None,
            "url": self.absolute_url(card.get("href", "").split("?")[0]),
        }


async def run(query: Optional[str] = None) -> Dict[str, Any]:
    return await FacebookMarketplaceScraper().run(query)
