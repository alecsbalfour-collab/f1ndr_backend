from scrapers.neighbourhood_scraper import NeighbourhoodScraper
from scrapers.used_scraper import UsedScraper

HTML = """
<div class="listing">
  <a class="listing-title" href="/classifieds/tools/dewalt-drill/123">DeWalt 20V drill</a>
  <span class="price">$120</span><span class="location">Calgary</span><time>Today</time>
</div>
"""


def test_parse():
    assert UsedScraper().parse(HTML) == [{
        "title": "DeWalt 20V drill", "price": "$120", "location": "Calgary", "posted": "Today",
        "url": "https://www.used.ca/classifieds/tools/dewalt-drill/123",
        "price_value": 120.0, "platform": "used",
    }]


def test_build_url():
    assert UsedScraper().build_url("drill") == "https://www.used.ca/classifieds/all?keywords=drill"


async def test_neighbourhood_rejects_unsupported_city_without_fetching():
    result = await NeighbourhoodScraper().run("Toronto")
    assert result["success"] is False
    assert "Unsupported city" in result["error"]


def test_neighbourhood_city_urls():
    scraper = NeighbourhoodScraper()
    assert scraper.build_url(None) == "https://www.usedcalgary.com/classifieds/cars"
    assert scraper.build_url("Edmonton") == "https://www.usededmonton.com/classifieds/cars"
