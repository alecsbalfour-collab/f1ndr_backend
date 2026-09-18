import pytest
from scrapers.facebook_scraper import run

def test_facebook_run():
    result = run("sofa")
    assert "source" in result
    assert isinstance(result.get("results", []), list)
