import pytest
from scrapers.kijiji_scraper import run, KijijiScraper

def test_kijiji_run_callable():
    """Test that the run function is callable."""
    assert callable(run)

def test_kijiji_scraper_class():
    """Test that the KijijiScraper class can be instantiated."""
    scraper = KijijiScraper()
    assert scraper.config is not None
    assert scraper.config.headless is True
