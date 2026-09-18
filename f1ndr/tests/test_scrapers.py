import pytest

def test_autotrader_scraper():
    from scrapers import run_autotrader
    assert callable(run_autotrader)


def test_kijiji_scraper():
    from scrapers import run_kijiji
    assert callable(run_kijiji)


def test_zillow_scraper():
    from scrapers import run_zillow
    assert callable(run_zillow)
