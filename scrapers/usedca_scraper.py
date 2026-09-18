from typing import Dict, List
from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper

BASE_URL = "https://www.usedcalgary.com/classifieds/cars"


class UsedCAScraper(BaseScraper):
    source_name = "usedca"

    def _run_internal(self) -> List[Dict[str, str]]:
        html = self.fetch_html(BASE_URL, wait_selector=".listing")
        if not html:
            return []
        return self.parse(html)

    def parse(self, html: str) -> List[Dict[str, str]]:
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select(".listing")

        listings = []
        for card in cards:
            title_el = card.select_one(".title")
            price_el = card.select_one(".price")
            link_el = card.select_one("a")

            if not title_el or not price_el or not link_el:
                continue

            listings.append({
                "title": title_el.get_text(strip=True),
                "price": price_el.get_text(strip=True),
                "url": link_el.get("href", "")
            })

        return listings


def run() -> Dict:
    scraper = UsedCAScraper()
    return scraper.run()
