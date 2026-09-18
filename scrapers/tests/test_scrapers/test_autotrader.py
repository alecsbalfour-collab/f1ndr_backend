import pytest
from scrapers.autotrader_scraper import run

def test_autotrader_run():
    result = run("car")
    assert "source" in result
    assert isinstance(result.get("results", []), list)
