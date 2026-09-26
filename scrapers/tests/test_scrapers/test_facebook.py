from scrapers.facebook_scraper import FacebookMarketplaceScraper

HTML = """
<div>
  <a href="/marketplace/item/1122334455/?ref=search">
    <span><span>CA$8,500</span></span><span>2012 Honda Accord</span>
    <span>Calgary, AB</span><span>180K km</span>
  </a>
  <a href="/marketplace/item/999/"><span>Free</span><span>Couch</span></a>
</div>
"""


def test_parse_reads_ordered_spans_and_dedupes_nested_text():
    assert FacebookMarketplaceScraper().parse(HTML) == [
        {"title": "2012 Honda Accord", "price": "CA$8,500", "location": "Calgary, AB",
         "mileage": "180K km", "url": "https://www.facebook.com/marketplace/item/1122334455/",
         "price_value": 8500.0, "platform": "facebook_marketplace"},
        {"title": "Couch", "price": "Free", "location": None, "mileage": None,
         "url": "https://www.facebook.com/marketplace/item/999/",
         "price_value": None, "platform": "facebook_marketplace"},
    ]


def test_parse_returns_empty_for_login_wall():
    assert FacebookMarketplaceScraper().parse("<form id='login_form'></form>") == []
