from scrapers.ebay_scraper import EbayScraper

HTML = """
<ul>
  <li class="s-item"><a class="s-item__link" href="https://ebay.com/itm/0"><div class="s-item__title">Shop on eBay</div></a></li>
  <li class="s-item">
    <a class="s-item__link" href="https://www.ebay.ca/itm/1234567890?hash=abc">
      <div class="s-item__title"><span>New Listing</span>ThinkPad X1 Carbon Gen 9</div></a>
    <span class="SECONDARY_INFO">Pre-Owned</span>
    <span class="s-item__price">C $899.99</span>
    <span class="s-item__location">from Canada</span>
  </li>
  <li class="s-card">
    <a class="su-link" href="https://www.ebay.ca/itm/555"><span class="s-card__title">Dell XPS 13</span></a>
    <span class="s-card__price">C $650.00</span>
  </li>
</ul>
"""


def test_parse_handles_legacy_and_current_markup_and_skips_promo_card():
    assert EbayScraper().parse(HTML) == [
        {"title": "ThinkPad X1 Carbon Gen 9", "price": "C $899.99", "location": "from Canada",
         "condition": "Pre-Owned", "url": "https://www.ebay.ca/itm/1234567890",
         "price_value": 899.99, "platform": "ebay"},
        {"title": "Dell XPS 13", "price": "C $650.00", "location": None, "condition": None,
         "url": "https://www.ebay.ca/itm/555", "price_value": 650.0, "platform": "ebay"},
    ]


def test_build_url():
    assert EbayScraper().build_url("thinkpad x1") == "https://www.ebay.ca/sch/i.html?_nkw=thinkpad+x1&_sacat=0"
