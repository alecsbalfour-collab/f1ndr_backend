from typing import Dict, List
from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper

# Full eBay search — not restricted to Motors
BASE_URL = "https://www.ebay.ca/sch/i.html?_nkw=vehicles&_sacat=0"


class EbayScraper(BaseScraper):
    source_name = "ebay"

    def run(self) -> Dict:
        html = self.fetch_html(BASE_URL)
        if not html:
            return {"source": self.source_name, "results": []}
        return {"source": self.source_name, "results": self.parse(html)}

    def parse(self, html: str) -> List[Dict[str, str]]:
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select(".s-item")

        listings: List[Dict[str, str]] = []

        for card in cards:
            title_el = card.select_one(".s-item__title")
            price_el = card.select_one(".s-item__price")
            link_el = card.select_one("a")

            if not title_el or not link_el:
                continue

            listings.append(
                {
                    "title": title_el.get_text(strip=True),
                    "price": price_el.get_text(strip=True) if price_el else "N/A",
                    "url": link_el.get("href") or "",
                }
            )

        return listings


def run(query: str = None) -> Dict:
    """Convenience function to run the ebay scraper."""
    scraper = EbayScraper()
    return scraper.run()
