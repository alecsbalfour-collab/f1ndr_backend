import pytest
from scrapers.craigslist_scraper import run, CraigslistScraper

def test_craigslist_run_callable():
    """Test that the run function is callable."""
    assert callable(run)

def test_craigslist_scraper_class():
    """Test that the CraigslistScraper class can be instantiated."""
    scraper = CraigslistScraper()
    assert scraper.config is not None
    assert scraper.config.headless is True
