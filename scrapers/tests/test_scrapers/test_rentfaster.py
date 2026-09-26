from scrapers.rentfaster_scraper import RentFasterScraper

HTML = """
<div class="listing-item">
  <a class="listing-link" href="/ab/calgary/rentals/apartment/1-bedroom/beltline/12345">
    <h3 class="listing-title">1 Bed Apartment in Beltline</h3></a>
  <span class="listing-price">$1,495</span>
  <span class="listing-details">1 bed, 1 bath</span>
  <span class="listing-community">Beltline</span>
</div>
"""


def test_parse():
    assert RentFasterScraper().parse(HTML) == [{
        "title": "1 Bed Apartment in Beltline", "price": "$1,495", "details": "1 bed, 1 bath",
        "location": "Beltline",
        "url": "https://www.rentfaster.ca/ab/calgary/rentals/apartment/1-bedroom/beltline/12345",
        "price_value": 1495.0, "platform": "rentfaster",
    }]
