import pytest
from scrapers.ebay_scraper import run

def test_ebay_run():
    result = run("laptop")
    assert "source" in result
    assert isinstance(result.get("results", []), list)
