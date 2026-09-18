import pytest
from scrapers.ebay_scraper import run, EbayScraper

def test_ebay_run_callable():
    """Test that the run function is callable."""
    assert callable(run)

def test_ebay_scraper_class():
    """Test that the EbayScraper class can be instantiated."""
    scraper = EbayScraper()
    assert scraper.config is not None
    assert scraper.config.headless is True
