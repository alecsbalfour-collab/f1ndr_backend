import pytest
from scrapers.zillow_scraper import run

def test_zillow_run():
    result = run("rent")
    assert "source" in result
    assert isinstance(result.get("results", []), list)
