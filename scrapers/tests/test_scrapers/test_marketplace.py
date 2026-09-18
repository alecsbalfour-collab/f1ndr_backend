import pytest
from scrapers.marketplace_scraper import run, MarketplaceScraper

def test_marketplace_run_callable():
    """Test that the run function is callable."""
    assert callable(run)

def test_marketplace_scraper_class():
    """Test that the MarketplaceScraper class can be instantiated."""
    scraper = MarketplaceScraper()
    assert scraper.config is not None
    assert scraper.config.headless is True
