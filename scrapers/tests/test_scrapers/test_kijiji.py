from scrapers.kijiji_scraper import KijijiScraper

HTML = """
<ul><li><section data-testid="listing-card">
  <a data-testid="listing-link" href="/v-cars-trucks/calgary/2016-mazda-3/1700000001">
    <h3 data-testid="listing-title">2016 Mazda 3 GS</h3></a>
  <p data-testid="listing-price">$11,200</p>
  <p data-testid="listing-location">Calgary</p>
  <p data-testid="listing-date">&lt; 5 minutes ago</p>
</section></li></ul>
"""


def test_parse():
    assert KijijiScraper().parse(HTML) == [{
        "title": "2016 Mazda 3 GS", "price": "$11,200", "location": "Calgary",
        "posted": "< 5 minutes ago",
        "url": "https://www.kijiji.ca/v-cars-trucks/calgary/2016-mazda-3/1700000001",
        "price_value": 11200.0, "platform": "kijiji",
    }]


def test_build_url_uses_slug():
    assert KijijiScraper().build_url("Mazda 3") == "https://www.kijiji.ca/b-calgary/mazda-3/k0l1700199"
