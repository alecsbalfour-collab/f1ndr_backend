from scrapers.realtor_scraper import run

def test_realtor():
    result = run()
    assert "source" in result
    assert isinstance(result.get("results", []), list)
