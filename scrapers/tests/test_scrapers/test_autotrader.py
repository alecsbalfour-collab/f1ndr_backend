import pytest
from scrapers.autotrader_scraper import run, AutotraderScraper

def test_autotrader_run_callable():
    """Test that the run function is callable."""
    assert callable(run)

def test_autotrader_scraper_class():
    """Test that the AutotraderScraper class can be instantiated."""
    scraper = AutotraderScraper()
    assert scraper.config is not None
    assert scraper.config.headless is True
