"""
Enterprise Realtor Scraper using Playwright

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


BASE_URL = "https://www.realtor.ca/map#ZoomLevel=11&Center=51.0447,-114.0719"


class RealtorScraper(BaseScraper):
    """Enterprise Realtor scraper with Playwright."""
    
    source_name = "realtor"
    
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
        Run the Realtor scraper with enterprise error handling.
        
        Args:
            query: Optional search query
            
        Returns:
            Dictionary with source and results
        """
        try:
            url = BASE_URL
            if query:
                url = f"https://www.realtor.ca/real-estate/{query}"
            
            logger.info(f"Starting Realtor scraper for URL: {url}")
            
            html = await self.fetch_html(
                url, 
                wait_selector=".listingCard"
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
        Parse Realtor HTML content with enterprise error handling.
        
        Args:
            html: HTML content to parse
            
        Returns:
            List of listing dictionaries
        """
        try:
            soup = BeautifulSoup(html, "html.parser")
            cards = soup.select(".listingCard")

            listings: List[Dict[str, str]] = []

            for card in cards:
                try:
                    title_el = card.select_one(".listingCardAddress")
                    price_el = card.select_one(".listingCardPrice")
                    link_el = card.select_one("a")
                    bedrooms_el = card.select_one(".listingCardBed")
                    bathrooms_el = card.select_one(".listingCardBath")

                    if not title_el or not link_el:
                        continue

                    listing = {
                        "title": title_el.get_text(strip=True),
                        "price": price_el.get_text(strip=True) if price_el else "N/A",
                        "url": link_el.get("href") or "",
                        "bedrooms": bedrooms_el.get_text(strip=True) if bedrooms_el else "N/A",
                        "bathrooms": bathrooms_el.get_text(strip=True) if bathrooms_el else "N/A",
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
    Convenience function to run the Realtor scraper.
    
    Args:
        query: Optional search query
        
    Returns:
        Scraper results dictionary
    """
    scraper = RealtorScraper()
    return await scraper.run(query)


def scrape_realtor(query: str = None):
    """Sync wrapper for run() function for backward compatibility."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(run(query))
