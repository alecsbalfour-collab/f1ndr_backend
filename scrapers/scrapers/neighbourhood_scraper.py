from typing import Dict, List
from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper

CITY_URLS = {
    "calgary": "https://www.usedcalgary.com/classifieds/cars",
    "edmonton": "https://www.usededmonton.com/classifieds/cars",
}

class NeighbourhoodScraper(BaseScraper):
    source_name = "neighbourhood_classifieds"

    def run(self, city: str) -> Dict:
        url = CITY_URLS.get(city.lower())
        if not url:
            return {"source": self.source_name, "results": []}

        html = self.fetch_html(url)
        if not html:
            return {"source": self.source_name, "results": []}

        return {
            "source": f"{self.source_name}_{city.lower()}",
            "results": self.parse(html),
        }

    def parse(self, html: str) -> List[Dict[str, str]]:
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select(".listing")

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
                    "url": link_el.get("href") or "",
                }
            )

        return listings
