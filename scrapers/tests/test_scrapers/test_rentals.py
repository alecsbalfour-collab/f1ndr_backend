from scrapers.rentals_scraper import RentalsScraper

HTML = """
<div class="listing-card">
  <a class="listing-card__details-link" href="/calgary/the-park-residences">
    <h2 class="listing-card__title">The Park Residences</h2></a>
  <p class="listing-card__price">$1,650 - $2,400</p>
  <ul class="listing-card__main-features">1-2 Beds</ul>
</div>
"""


def test_parse():
    assert RentalsScraper().parse(HTML) == [{
        "title": "The Park Residences", "price": "$1,650 - $2,400", "details": "1-2 Beds",
        "url": "https://rentals.ca/calgary/the-park-residences",
        "price_value": 1650.0, "platform": "rentals_ca",
    }]


def test_build_url_uses_city_slug():
    assert RentalsScraper().build_url("Edmonton") == "https://rentals.ca/edmonton"
