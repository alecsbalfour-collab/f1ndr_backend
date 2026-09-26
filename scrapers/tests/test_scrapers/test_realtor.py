from scrapers.realtor_scraper import RealtorScraper

HTML = """
<div class="cardCon">
  <a class="blockLink" href="/real-estate/27000000/123-main-st-calgary">
    <div class="smallListingCardPrice">$549,900</div>
    <div class="smallListingCardAddress">123 Main St, Calgary, Alberta</div>
    <div class="smallListingCardIconCon">3 bd 2 ba</div>
  </a>
</div>
"""


def test_parse():
    assert RealtorScraper().parse(HTML) == [{
        "title": "123 Main St, Calgary, Alberta", "price": "$549,900", "details": "3 bd 2 ba",
        "url": "https://www.realtor.ca/real-estate/27000000/123-main-st-calgary",
        "price_value": 549900.0, "platform": "realtor",
    }]


def test_build_url_uses_city_slug():
    assert RealtorScraper().build_url("Red Deer") == "https://www.realtor.ca/ab/red-deer/real-estate"
