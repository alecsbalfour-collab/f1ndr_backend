def test_autotrader_scraper():
    from scrapers import run_autotrader
    result = run_autotrader("cars")
    assert "source" in result


def test_kijiji_scraper():
    from scrapers import run_kijiji
    result = run_kijiji("rentals")
    assert "source" in result


def test_zillow_scraper():
    from scrapers import run_zillow
    result = run_zillow("homes")
    assert "source" in result
