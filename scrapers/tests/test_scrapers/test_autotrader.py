from scrapers.autotrader_scraper import AutotraderScraper

HTML = """
<div class="result-item">
  <a class="inner-link" href="/a/honda/civic/calgary/alberta/5_123_abc/">
    <span class="title-with-trim">2019 Honda Civic LX</span></a>
  <span class="price-amount">$19,995</span>
  <span class="proximity-text">Calgary, AB</span>
  <span class="odometer-proximity">54,000 km</span>
</div>
"""


def test_parse():
    assert AutotraderScraper().parse(HTML) == [{
        "title": "2019 Honda Civic LX", "price": "$19,995", "location": "Calgary, AB",
        "mileage": "54,000 km",
        "url": "https://www.autotrader.ca/a/honda/civic/calgary/alberta/5_123_abc/",
        "price_value": 19995.0, "platform": "autotrader",
    }]


def test_build_url():
    assert AutotraderScraper().build_url("civic lx").endswith("&kwd=civic+lx")
