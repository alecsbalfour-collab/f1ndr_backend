from scrapers.craigslist_scraper import CraigslistScraper

HTML = """
<ol><li class="cl-static-search-result" title="Trek mountain bike">
  <a href="https://calgary.craigslist.org/bik/d/calgary-trek/7712345678.html">
    <div class="title">Trek mountain bike</div>
    <div class="details"><div class="price">$450</div><div class="location">NW Calgary</div></div>
  </a>
</li></ol>
"""


def test_parse():
    assert CraigslistScraper().parse(HTML) == [{
        "title": "Trek mountain bike", "price": "$450", "location": "NW Calgary",
        "url": "https://calgary.craigslist.org/bik/d/calgary-trek/7712345678.html",
        "price_value": 450.0, "platform": "craigslist",
    }]


def test_build_url():
    assert CraigslistScraper().build_url("road bike") == "https://calgary.craigslist.org/search/sss?query=road+bike"
