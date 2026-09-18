import pytest
from scrapers.used_scraper import run, UsedScraper

def test_used_run_callable():
    """Test that the run function is callable."""
    assert callable(run)

def test_used_scraper_class():
    """Test that the UsedScraper class can be instantiated."""
    scraper = UsedScraper()
    assert scraper.config is not None
    assert scraper.config.headless is True
