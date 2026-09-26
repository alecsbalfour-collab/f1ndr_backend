"""
Basic tests for f1ndr core.
"""

from f1ndr.core.core import run_search, run_intelligence
from f1ndr.db.db import save_listing


def test_search_and_intelligence_flow():
    listing = {
        "id": 1,
        "vin": "TESTVIN1234567890",
        "title": "2015 Subaru Outback Limited",
        "description": "Well maintained, single owner.",
        "make": "Subaru",
        "model": "Outback",
        "year": 2015,
        "price": 18000,
        "mileage": 120000,
        "location": "Calgary",
    }

    save_listing(listing)

    search_result = run_search({"make": "Subaru", "model": "Outback"})
    assert len(search_result["results"]) >= 1

    intel_result = run_intelligence(listing)
    assert "market_value" in intel_result
    assert "fraud" in intel_result
