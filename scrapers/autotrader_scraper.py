"""
Enterprise Autotrader Scraper using Playwright

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


BASE_URL = (
    "https://www.autotrader.ca/cars/?rcp=100&rcs=0&prx=100&loc=T2A&hprc=True&wcp=True"
)


class AutotraderScraper(BaseScraper):
    """Enterprise Autotrader scraper with Playwright."""
    
    source_name = "autotrader"
    
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
        Run the Autotrader scraper with enterprise error handling.
        
        Args:
            query: Optional search query
            
        Returns:
            Dictionary with source and results
        """
        try:
            url = BASE_URL
            if query:
                # Add query parameter if provided
                url = f"{BASE_URL}&q={query}"
            
            logger.info(f"Starting Autotrader scraper for URL: {url}")
            
            html = await self.fetch_html(
                url, 
                wait_selector=".result-item"
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
        Parse Autotrader HTML content with enterprise error handling.
        
        Args:
            html: HTML content to parse
            
        Returns:
            List of listing dictionaries
        """
        try:
            soup = BeautifulSoup(html, "html.parser")
            cards = soup.select(".result-item")

            listings: List[Dict[str, str]] = []

            for card in cards:
                try:
                    title_el = card.select_one(".result-title")
                    price_el = card.select_one(".price-amount")
                    link_el = card.select_one("a")
                    location_el = card.select_one(".result-location")
                    mileage_el = card.select_one(".distance")

                    if not title_el or not link_el:
                        continue

                    listing = {
                        "title": title_el.get_text(strip=True),
                        "price": price_el.get_text(strip=True) if price_el else "N/A",
                        "url": "https://www.autotrader.ca" + (link_el.get("href") or ""),
                        "location": location_el.get_text(strip=True) if location_el else "N/A",
                        "mileage": mileage_el.get_text(strip=True) if mileage_el else "N/A",
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
    Convenience function to run the Autotrader scraper.
    
    Args:
        query: Optional search query
        
    Returns:
        Scraper results dictionary
    """
    scraper = AutotraderScraper()
    return await scraper.run(query)
