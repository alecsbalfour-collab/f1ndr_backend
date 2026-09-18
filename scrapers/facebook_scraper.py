from typing import Dict, List

from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper

BASE_URL = "https://www.facebook.com/marketplace/106199279413606/vehicles"


class FacebookMarketplaceScraper(BaseScraper):
    source_name = "facebook_marketplace"

    def _run_internal(self) -> List[Dict[str, str]]:
        html = self.fetch_html(BASE_URL, wait_selector="div[role='article']")
        if not html:
            return []
        return self.parse(html)

    def parse(self, html: str) -> List[Dict[str, str]]:
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select("div[role='article']")

        listings: List[Dict[str, str]] = []
        for card in cards:
            title_el = card.find("span")
            price_el = card.find("span", string=lambda s: s and "$" in s)

            if not title_el or not price_el:
                continue

            listings.append(
                {
                    "title": title_el.get_text(strip=True),
                    "price": price_el.get_text(strip=True),
                }
            )

        return listings


def run(query: str = None) -> Dict:
    """Convenience function to run the facebook scraper."""
    scraper = FacebookMarketplaceScraper()
    return scraper.run()
