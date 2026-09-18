from typing import Dict, List
from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper

BASE_URL = "https://www.realtor.ca/map#ZoomLevel=11&Center=51.0447,-114.0719"


class RealtorScraper(BaseScraper):
    source_name = "realtor"

    def run(self) -> Dict:
        html = self.fetch_html(BASE_URL)
        if not html:
            return {"source": self.source_name, "results": []}
        return {"source": self.source_name, "results": self.parse(html)}

    def parse(self, html: str) -> List[Dict[str, str]]:
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select(".listingCard")

        listings: List[Dict[str, str]] = []

        for card in cards:
            title_el = card.select_one(".listingCardAddress")
            price_el = card.select_one(".listingCardPrice")
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
    """Convenience function to run the realtor scraper."""
    scraper = RealtorScraper()
    return scraper.run()


def scrape_realtor(query: str = None) -> Dict:
    """Alias for run() function."""
    return run(query)
