import pytest
from scrapers.usedca_scraper import run, UsedCAScraper

def test_usedca_run_callable():
    """Test that the run function is callable."""
    assert callable(run)

def test_usedca_scraper_class():
    """Test that the UsedCAScraper class can be instantiated."""
    scraper = UsedCAScraper()
    assert scraper.config is not None
    assert scraper.config.headless is True
