import pytest
from scrapers.rentfaster_scraper import run, RentFasterScraper

def test_rentfaster_run_callable():
    """Test that the run function is callable."""
    assert callable(run)

def test_rentfaster_scraper_class():
    """Test that the RentFasterScraper class can be instantiated."""
    scraper = RentFasterScraper()
    assert scraper.config is not None
    assert scraper.config.headless is True
