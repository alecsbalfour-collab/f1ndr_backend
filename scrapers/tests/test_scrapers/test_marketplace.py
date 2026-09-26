from scrapers.marketplace_scraper import MarketplaceScraper

HTML = '<a href="/marketplace/item/42/"><span>$60</span><span>Office chair</span><span>Airdrie, AB</span></a>'


def test_parse_uses_its_own_platform_name():
    [listing] = MarketplaceScraper().parse(HTML)
    assert listing["title"] == "Office chair"
    assert listing["platform"] == "marketplace"


def test_build_url():
    scraper = MarketplaceScraper()
    assert scraper.build_url(None) == "https://www.facebook.com/marketplace/calgary/"
    assert scraper.build_url("chair") == "https://www.facebook.com/marketplace/calgary/search?query=chair"
