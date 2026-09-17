from typing import Dict, List
from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper

BASE_URL = "https://www.kijiji.ca/b-cars-vehicles/calgary/c174l1700199"


class KijijiScraper(BaseScraper):
    source_name = "kijiji"

    def run(self) -> Dict:
        html = self.fetch_html(BASE_URL)
        if not html:
            return {"source": self.source_name, "results": []}
        return {"source": self.source_name, "results": self.parse(html)}

    def parse(self, html: str) -> List[Dict[str, str]]:
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select(".search-item")

        listings: List[Dict[str, str]] = []

        for card in cards:
            title_el = card.select_one(".title")
            price_el = card.select_one(".price")
            link_el = card.select_one("a")

            if not title_el or not link_el:
                continue

            listings.append(
                {
                    "title": title_el.get_text(strip=True),
                    "price": price_el.get_text(strip=True) if price_el else "N/A",
                    "url": "https://www.kijiji.ca" + (link_el.get("href") or ""),
                }
            )

        return listings
