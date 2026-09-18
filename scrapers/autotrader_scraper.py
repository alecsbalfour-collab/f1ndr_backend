from typing import Dict, List
from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper

BASE_URL = (
    "https://www.autotrader.ca/cars/?rcp=100&rcs=0&prx=100&loc=T2A&hprc=True&wcp=True"
)


class AutotraderScraper(BaseScraper):
    source_name = "autotrader"

    def run(self) -> Dict:
        html = self.fetch_html(BASE_URL)
        if not html:
            return {"source": self.source_name, "results": []}
        return {"source": self.source_name, "results": self.parse(html)}

    def parse(self, html: str) -> List[Dict[str, str]]:
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select(".result-item")

        listings: List[Dict[str, str]] = []

        for card in cards:
            title_el = card.select_one(".result-title")
            price_el = card.select_one(".price-amount")
            link_el = card.select_one("a")

            if not title_el or not price_el or not link_el:
                continue

            listings.append(
                {
                    "title": title_el.get_text(strip=True),
                    "price": price_el.get_text(strip=True),
                    "url": "https://www.autotrader.ca"
                    + (link_el.get("href") or ""),
                }
            )

        return listings


def run(query: str = None) -> Dict:
    """Convenience function to run the autotrader scraper."""
    scraper = AutotraderScraper()
    return scraper.run()
