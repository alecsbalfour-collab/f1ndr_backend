import pytest
from scrapers.rentfaster_scraper import run

def test_rentfaster_run():
    result = run("condo")
    assert "source" in result
    assert isinstance(result.get("results", []), list)
