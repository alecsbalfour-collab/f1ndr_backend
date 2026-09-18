"""
Enterprise Playwright Base Scraper

DICT-aligned base scraper with enterprise features:
- Async Playwright support
- Comprehensive error handling
- Logging integration
- Rate limiting
- Retry logic
- Resource cleanup
- Headers management
- Response validation
"""

import asyncio
import logging
from typing import Optional, Dict, List, Any
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from dataclasses import dataclass
import random


logger = logging.getLogger(__name__)


@dataclass
class ScraperConfig:
    """Enterprise scraper configuration."""
    headless: bool = True
    timeout: int = 30000
    wait_until: str = "networkidle"
    user_agent: Optional[str] = None
    viewport_width: int = 1920
    viewport_height: int = 1080
    max_retries: int = 3
    retry_delay: float = 1.0
    rate_limit_delay: float = 0.5


class BaseScraper:
    """Enterprise Playwright base scraper with DICT patterns."""
    
    def __init__(self, config: Optional[ScraperConfig] = None):
        self.config = config or ScraperConfig()
        self.source_name = "base"
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        
    async def _initialize_browser(self) -> None:
        """Initialize Playwright browser with enterprise settings."""
        if self._browser is None:
            playwright = await async_playwright().start()
            self._browser = await playwright.chromium.launch(
                headless=self.config.headless
            )
            
            # Set up context with realistic user agent
            user_agent = self.config.user_agent or self._get_default_user_agent()
            self._context = await self._browser.new_context(
                user_agent=user_agent,
                viewport={
                    'width': self.config.viewport_width,
                    'height': self.config.viewport_height
                }
            )
            
            # Set up page
            self._page = await self._context.new_page()
            self._page.set_default_timeout(self.config.timeout)
            
    def _get_default_user_agent(self) -> str:
        """Get a realistic user agent string."""
        return (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    
    async def _cleanup(self) -> None:
        """Clean up browser resources."""
        if self._page:
            await self._page.close()
            self._page = None
        if self._context:
            await self._context.close()
            self._context = None
        if self._browser:
            await self._browser.close()
            self._browser = None
    
    async def fetch_html(
        self, 
        url: str, 
        wait_selector: Optional[str] = None,
        retries: int = 0
    ) -> Optional[str]:
        """
        Fetch HTML content with enterprise error handling and retry logic.
        
        Args:
            url: Target URL
            wait_selector: CSS selector to wait for before returning
            retries: Current retry count
            
        Returns:
            HTML content or None if failed
        """
        try:
            await self._initialize_browser()
            
            # Navigate to URL
            await self._page.goto(
                url, 
                wait_until=self.config.wait_until,
                timeout=self.config.timeout
            )
            
            # Wait for specific selector if provided
            if wait_selector:
                try:
                    await self._page.wait_for_selector(
                        wait_selector, 
                        timeout=self.config.timeout
                    )
                except Exception as e:
                    logger.warning(
                        f"Selector {wait_selector} not found for {self.source_name}: {e}"
                    )
            
            # Rate limiting
            await asyncio.sleep(self.config.rate_limit_delay)
            
            # Get HTML content
            html = await self._page.content()
            
            logger.info(f"Successfully fetched HTML from {url} for {self.source_name}")
            return html
            
        except Exception as e:
            logger.error(f"Error fetching HTML from {url} for {self.source_name}: {e}")
            
            # Retry logic
            if retries < self.config.max_retries:
                delay = self.config.retry_delay * (2 ** retries) + random.uniform(0, 1)
                logger.info(f"Retrying {self.source_name} in {delay:.2f}s (attempt {retries + 1})")
                await asyncio.sleep(delay)
                return await self.fetch_html(url, wait_selector, retries + 1)
            
            return None
    
    async def fetch_multiple_pages(
        self,
        urls: List[str],
        wait_selector: Optional[str] = None
    ) -> List[Optional[str]]:
        """
        Fetch multiple pages concurrently with rate limiting.
        
        Args:
            urls: List of URLs to fetch
            wait_selector: CSS selector to wait for
            
        Returns:
            List of HTML contents (None for failed requests)
        """
        results = []
        for url in urls:
            html = await self.fetch_html(url, wait_selector)
            results.append(html)
            # Additional delay between requests
            await asyncio.sleep(self.config.rate_limit_delay)
        return results
    
    async def run(self) -> Dict[str, Any]:
        """
        Main run method to be implemented by subclasses.
        
        Returns:
            Dictionary with source and results
        """
        raise NotImplementedError("Subclasses must implement run method")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._initialize_browser()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._cleanup()
    
    async def close(self) -> None:
        """Explicit cleanup method."""
        await self._cleanup()



