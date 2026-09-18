import pytest
from scrapers.rentals_scraper import run

def test_rentals_run():
    result = run("apartment")
    assert "source" in result
    assert isinstance(result.get("results", []), list)
