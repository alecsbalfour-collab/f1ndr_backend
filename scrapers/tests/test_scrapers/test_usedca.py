import pytest
from scrapers.usedca_scraper import run

def test_usedca_run():
    result = run("furniture")
    assert "success" in result
    assert isinstance(result.get("listings", []), list)
