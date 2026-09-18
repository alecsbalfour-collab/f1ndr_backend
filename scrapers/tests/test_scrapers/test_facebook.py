import pytest
from scrapers.facebook_scraper import run, FacebookMarketplaceScraper

def test_facebook_run_callable():
    """Test that the run function is callable."""
    assert callable(run)

def test_facebook_scraper_class():
    """Test that the FacebookMarketplaceScraper class can be instantiated."""
    scraper = FacebookMarketplaceScraper()
    assert scraper.config is not None
    assert scraper.config.headless is True
