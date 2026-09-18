"""
Enterprise Neighbourhood Scraper using Playwright

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


CITY_URLS = {
    "calgary": "https://www.usedcalgary.com/classifieds/cars",
    "edmonton": "https://www.usededmonton.com/classifieds/cars",
}


class NeighbourhoodScraper(BaseScraper):
    """Enterprise Neighbourhood scraper with Playwright."""
    
    source_name = "neighbourhood_classifieds"
    
    def __init__(self, config: ScraperConfig = None):
        super().__init__(config or ScraperConfig(
            headless=True,
            timeout=30000,
            wait_until="networkidle",
            max_retries=3,
            rate_limit_delay=1.0
        ))

    async def run(self, city: str = "calgary") -> Dict[str, Any]:
        """
        Run the Neighbourhood scraper with enterprise error handling.
        
        Args:
            city: City name (calgary, edmonton)
            
        Returns:
            Dictionary with source and results
        """
        try:
            url = CITY_URLS.get(city.lower())
            if not url:
                logger.warning(f"Unsupported city: {city}")
                return {
                    "source": self.source_name, 
                    "results": [],
                    "error": f"Unsupported city: {city}"
                }

            logger.info(f"Starting Neighbourhood scraper for {city}: {url}")
            
            html = await self.fetch_html(
                url, 
                wait_selector=".listing"
            )
            
            if not html:
                logger.warning(f"No HTML content retrieved for {self.source_name}")
                return {
                    "source": f"{self.source_name}_{city.lower()}", 
                    "results": [],
                    "error": "Failed to fetch HTML content"
                }
            
            listings = self.parse(html)
            logger.info(f"Successfully parsed {len(listings)} listings from {self.source_name}")
            
            return {
                "source": f"{self.source_name}_{city.lower()}", 
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
        Parse Neighbourhood HTML content with enterprise error handling.
        
        Args:
            html: HTML content to parse
            
        Returns:
            List of listing dictionaries
        """
        try:
            soup = BeautifulSoup(html, "html.parser")
            cards = soup.select(".listing")

            listings: List[Dict[str, str]] = []

            for card in cards:
                try:
                    title_el = card.select_one(".title")
                    price_el = card.select_one(".price")
                    link_el = card.select_one("a")
                    location_el = card.select_one(".location")

                    if not title_el or not link_el:
                        continue

                    listing = {
                        "title": title_el.get_text(strip=True),
                        "price": price_el.get_text(strip=True) if price_el else "N/A",
                        "url": link_el.get("href") or "",
                        "location": location_el.get_text(strip=True) if location_el else "N/A",
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
    Convenience function to run the Neighbourhood scraper.
    
    Args:
        query: City name (calgary, edmonton)
        
    Returns:
        Scraper results dictionary
    """
    scraper = NeighbourhoodScraper()
    return await scraper.run(query or "calgary")
