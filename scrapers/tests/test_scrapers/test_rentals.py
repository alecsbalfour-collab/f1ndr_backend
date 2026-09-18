import pytest
from scrapers.rentals_scraper import run, RentalsScraper

def test_rentals_run_callable():
    """Test that the run function is callable."""
    assert callable(run)

def test_rentals_scraper_class():
    """Test that the RentalsScraper class can be instantiated."""
    scraper = RentalsScraper()
    assert scraper.config is not None
    assert scraper.config.headless is True
