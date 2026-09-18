import pytest
from scrapers.craigslist_scraper import run

def test_craigslist_run():
    result = run("bike")
    assert "source" in result
    assert isinstance(result.get("results", []), list)
