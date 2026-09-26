from scrapers.usedca_scraper import UsedCAScraper

HTML = """
<div class="listing">
  <a class="title" href="/classifieds/cars/2014-jeep-wrangler/987">2014 Jeep Wrangler</a>
  <span class="price">$24,000</span>
</div>
"""


def test_parse():
    [listing] = UsedCAScraper().parse(HTML)
    assert listing["title"] == "2014 Jeep Wrangler"
    assert listing["url"] == "https://www.usedcalgary.com/classifieds/cars/2014-jeep-wrangler/987"
    assert listing["price_value"] == 24000.0
    assert listing["platform"] == "usedca"
