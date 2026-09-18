import pytest
from scrapers.zillow_scraper import run, ZillowScraper

def test_zillow_run_callable():
    """Test that the run function is callable."""
    assert callable(run)

def test_zillow_scraper_class():
    """Test that the ZillowScraper class can be instantiated."""
    scraper = ZillowScraper()
    assert scraper.config is not None
    assert scraper.config.headless is True
