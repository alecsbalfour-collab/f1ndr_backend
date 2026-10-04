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


def test_search_filters_by_category():
    save_listing({"id": "cat-rv", "title": "Fifth Wheel", "category": "vehicles", "subcategory": "fifth_wheel", "price": 40000})
    save_listing({"id": "cat-goods", "title": "Sofa", "category": "goods", "price": 300})
    save_listing({"id": "cat-legacy", "title": "Mystery", "price": 7500})

    found = {r.get("id") for r in run_search({"subcategory": "fifth_wheel"})["results"]}
    assert "cat-rv" in found and "cat-goods" not in found
    found = {r.get("id") for r in run_search({"category": "vehicles"})["results"]}
    assert "cat-rv" in found and "cat-goods" not in found
    # Documents without a category land in "other" rather than guessing vehicles.
    found = {r.get("id") for r in run_search({"category": "other"})["results"]}
    assert "cat-legacy" in found and "cat-rv" not in found
