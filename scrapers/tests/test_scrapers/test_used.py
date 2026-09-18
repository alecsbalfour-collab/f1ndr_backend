import pytest
from scrapers.used_scraper import run

def test_used_run():
    result = run("tools")
    assert "success" in result
    assert isinstance(result.get("listings", []), list)
