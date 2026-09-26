from scrapers.locanto_scraper import LocantoScraper

HTML = """
<article class="posting_listing">
  <a class="posting_listing__title" href="/ID_5012345678/2010-Toyota-Tacoma.html">2010 Toyota Tacoma</a>
  <span class="posting_listing__price">$16,500</span>
  <span class="posting_listing__city">Calgary</span>
</article>
"""


def test_parse():
    assert LocantoScraper().parse(HTML) == [{
        "title": "2010 Toyota Tacoma", "price": "$16,500", "location": "Calgary",
        "url": "https://calgary.locanto.ca/ID_5012345678/2010-Toyota-Tacoma.html",
        "price_value": 16500.0, "platform": "locanto",
    }]
