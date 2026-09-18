import pytest
from scrapers.realtor_scraper import run, RealtorScraper

def test_realtor_run_callable():
    """Test that the run function is callable."""
    assert callable(run)

def test_realtor_scraper_class():
    """Test that the RealtorScraper class can be instantiated."""
    scraper = RealtorScraper()
    assert scraper.config is not None
    assert scraper.config.headless is True
