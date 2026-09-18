import pytest
from scrapers.marketplace_scraper import run

def test_marketplace_run():
    result = run("chair")
    assert "source" in result
    assert isinstance(result.get("results", []), list)
