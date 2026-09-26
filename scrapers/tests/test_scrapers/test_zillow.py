from scrapers.zillow_scraper import ZillowScraper

HTML = """
<ul><li><article data-test="property-card">
  <a data-test="property-card-link" href="https://www.zillow.com/homedetails/1-Main-St/123_zpid/">
    <address data-test="property-card-addr">1 Main St, Calgary, AB</address></a>
  <span data-test="property-card-price">C$689,000</span>
  <ul class="StyledPropertyCardHomeDetailsList">4 bds 3 ba</ul>
</article></li></ul>
"""


def test_parse():
    assert ZillowScraper().parse(HTML) == [{
        "title": "1 Main St, Calgary, AB", "price": "C$689,000", "details": "4 bds 3 ba",
        "url": "https://www.zillow.com/homedetails/1-Main-St/123_zpid/",
        "price_value": 689000.0, "platform": "zillow",
    }]


def test_build_url_uses_slug():
    assert ZillowScraper().build_url("Calgary AB") == "https://www.zillow.com/homes/calgary-ab_rb/"
