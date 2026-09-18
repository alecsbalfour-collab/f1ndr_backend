"""
Enterprise Kijiji Scraper using Playwright

DICT-aligned scraper with enterprise features:
- Async Playwright support
- Comprehensive error handling
- Logging integration
- Rate limiting
- Retry logic
"""

import asyncio
import logging
from typing import Dict, List, Any
from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper, ScraperConfig


logger = logging.getLogger(__name__)


BASE_URL = "https://www.kijiji.ca/b-cars-vehicles/calgary/c174l1700199"


class KijijiScraper(BaseScraper):
    """Enterprise Kijiji scraper with Playwright."""
    
    source_name = "kijiji"
    
    def __init__(self, config: ScraperConfig = None):
        super().__init__(config or ScraperConfig(
            headless=True,
            timeout=30000,
            wait_until="networkidle",
            max_retries=3,
            rate_limit_delay=1.0
        ))

    async def run(self, query: str = None) -> Dict[str, Any]:
        """
        Run the Kijiji scraper with enterprise error handling.
        
        Args:
            query: Optional search query
            
        Returns:
            Dictionary with source and results
        """
        try:
            url = BASE_URL
            if query:
                url = f"https://www.kijiji.ca/b-search.html?dc=true&query={query}"
            
            logger.info(f"Starting Kijiji scraper for URL: {url}")
            
            html = await self.fetch_html(
                url, 
                wait_selector=".search-item"
            )
            
            if not html:
                logger.warning(f"No HTML content retrieved for {self.source_name}")
                return {
                    "source": self.source_name, 
                    "results": [],
                    "error": "Failed to fetch HTML content"
                }
            
            listings = self.parse(html)
            logger.info(f"Successfully parsed {len(listings)} listings from {self.source_name}")
            
            return {
                "source": self.source_name, 
                "results": listings,
                "count": len(listings),
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Error in {self.source_name} scraper: {e}")
            return {
                "source": self.source_name, 
                "results": [],
                "error": str(e)
            }
        finally:
            await self._cleanup()

    def parse(self, html: str) -> List[Dict[str, str]]:
        """
        Parse Kijiji HTML content with enterprise error handling.
        
        Args:
            html: HTML content to parse
            
        Returns:
            List of listing dictionaries
        """
        try:
            soup = BeautifulSoup(html, "html.parser")
            cards = soup.select(".search-item")

            listings: List[Dict[str, str]] = []

            for card in cards:
                try:
                    title_el = card.select_one(".title")
                    price_el = card.select_one(".price")
                    link_el = card.select_one("a")
                    location_el = card.select_one(".location")
                    date_el = card.select_one(".date-posted")

                    if not title_el or not link_el:
                        continue

                    listing = {
                        "title": title_el.get_text(strip=True),
                        "price": price_el.get_text(strip=True) if price_el else "N/A",
                        "url": "https://www.kijiji.ca" + (link_el.get("href") or ""),
                        "location": location_el.get_text(strip=True) if location_el else "N/A",
                        "date": date_el.get_text(strip=True) if date_el else "N/A",
                        "platform": self.source_name
                    }
                    
                    listings.append(listing)
                    
                except Exception as e:
                    logger.warning(f"Error parsing individual listing: {e}")
                    continue

            return listings
            
        except Exception as e:
            logger.error(f"Error parsing HTML content: {e}")
            return []


async def run(query: str = None) -> Dict[str, Any]:
    """
    Convenience function to run the Kijiji scraper.
    
    Args:
        query: Optional search query
        
    Returns:
        Scraper results dictionary
    """
    scraper = KijijiScraper()
    return await scraper.run(query)
