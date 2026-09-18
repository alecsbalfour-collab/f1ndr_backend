import pytest
from scrapers.kijiji_scraper import run

def test_kijiji_run():
    result = run("sofa")
    assert "source" in result
    assert isinstance(result.get("results", []), list)
