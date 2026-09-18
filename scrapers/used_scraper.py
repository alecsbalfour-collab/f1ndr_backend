"""
Enterprise Used.ca Scraper using Playwright

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


PLATFORM = "used"


class UsedScraper(BaseScraper):
    """Enterprise Used.ca scraper with Playwright."""
    
    source_name = "used"
    
    def __init__(self, config: ScraperConfig = None):
        super().__init__(config or ScraperConfig(
            headless=True,
            timeout=30000,
            wait_until="networkidle",
            max_retries=3,
            rate_limit_delay=1.0
        ))

    def build_url(self, query: str = None) -> str:
        """Build URL for Used.ca search."""
        base = "https://www.used.ca/search/?q="
        return f"{base}{query or ''}"

    async def run(self, query: str = None) -> Dict[str, Any]:
        """
        Run the Used.ca scraper with enterprise error handling.
        
        Args:
            query: Optional search query
            
        Returns:
            Dictionary with source and results
        """
        try:
            url = self.build_url(query)
            logger.info(f"Starting Used.ca scraper for URL: {url}")
            
            html = await self.fetch_html(
                url, 
                wait_selector=".listing"
            )
            
            if not html:
                logger.warning(f"No HTML content retrieved for {self.source_name}")
                return {
                    "success": False,
                    "listings": [],
                    "error": "Failed to fetch HTML content"
                }
            
            listings = self.parse_html(html)
            logger.info(f"Successfully parsed {len(listings)} listings from {self.source_name}")
            
            return {
                "success": True,
                "listings": listings,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Error in {self.source_name} scraper: {e}")
            return {
                "success": False,
                "listings": [],
                "error": str(e)
            }
        finally:
            await self._cleanup()

    def parse_html(self, html: str) -> List[Dict[str, Any]]:
        """
        Parse Used.ca HTML content with enterprise error handling.
        
        Args:
            html: HTML content to parse
            
        Returns:
            List of listing dictionaries
        """
        try:
            if not html:
                return []

            soup = BeautifulSoup(html, "html.parser")
            listings = []

            for item in soup.select(".listing"):
                try:
                    listing = {
                        "title": item.select_one(".title").get_text(strip=True) if item.select_one(".title") else None,
                        "price": item.select_one(".price").get_text(strip=True) if item.select_one(".price") else None,
                        "url": item.select_one("a")["href"] if item.select_one("a") else None,
                        "image": item.select_one("img")["src"] if item.select_one("img") else None,
                        "location": item.select_one(".location").get_text(strip=True) if item.select_one(".location") else None,
                        "posted_at": None,
                        "platform": PLATFORM,
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
    Convenience function to run the Used.ca scraper.
    
    Args:
        query: Optional search query
        
    Returns:
        Scraper results dictionary
    """
    scraper = UsedScraper()
    return await scraper.run(query)
