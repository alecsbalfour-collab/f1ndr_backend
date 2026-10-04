"""
Core logic for f1ndr.
"""

from f1ndr.config.config import get_f1ndr_config
from f1ndr.data.data import serialize_listing
from f1ndr.db.db import query_listings, save_listing
from f1ndr.utils.utils import (
    normalize_listing,
    decode_vin,
    compute_market_value,
    detect_duplicates,
    detect_fraud,
)


def run_search(params: dict) -> dict:
    """
    Perform a search over stored listings using simple filters.
    params may include: category, subcategory, make, model, year_min, year_max, price_min, price_max, text.
    """
    config = get_f1ndr_config()
    listings = query_listings()

    category = params.get("category")
    subcategory = params.get("subcategory")
    make = params.get("make")
    model = params.get("model")
    year_min = params.get("year_min")
    year_max = params.get("year_max")
    price_min = params.get("price_min")
    price_max = params.get("price_max")
    text = params.get("text", "").lower().strip()

    def matches(l: dict) -> bool:
        # Listings without a category/subcategory land in "other" rather than guessing.
        if category and (l.get("category") or "other") != category:
            return False
        if subcategory and (l.get("subcategory") or "other") != subcategory:
            return False
        if make and l.get("make") != make:
            return False
        if model and l.get("model") != model:
            return False
        year = l.get("year")
        if year_min and year and year < year_min:
            return False
        if year_max and year and year > year_max:
            return False
        price = l.get("price")
        if price_min and price and price < price_min:
            return False
        if price_max and price and price > price_max:
            return False
        if text:
            blob = " ".join(
                str(v).lower()
                for v in [
                    l.get("title", ""),
                    l.get("description", ""),
                    l.get("make", ""),
                    l.get("model", ""),
                ]
            )
            if text not in blob:
                return False
        return True

    filtered = [serialize_listing(normalize_listing(l)) for l in listings if matches(l)]

    sort_key = config["default_sort"]
    if sort_key == "price":
        filtered.sort(key=lambda x: x.get("price") or 0)
    elif sort_key == "year":
        filtered.sort(key=lambda x: x.get("year") or 0, reverse=True)

    return {"results": filtered[: config["max_results"]]}


def run_intelligence(listing: dict) -> dict:
    """
    Run VIN decode, market value, duplicate detection, and fraud scoring on a single listing.
    """
    config = get_f1ndr_config()
    listing = normalize_listing(listing)
    result: dict = {}

    if config["enable_vin"] and listing.get("vin"):
        result["vin"] = decode_vin(listing["vin"])

    if config["enable_market_value"]:
        result["market_value"] = compute_market_value(listing)

    if config["enable_duplicates"]:
        all_listings = query_listings()
        result["duplicates"] = detect_duplicates(
            listing,
            all_listings,
            title_threshold=config["duplicate_title_threshold"],
            price_delta=config["duplicate_price_delta"],
        )

    if config["enable_fraud"]:
        result["fraud"] = detect_fraud(
            listing,
            price_floor_factor=config["fraud_price_floor_factor"],
            price_ceiling_factor=config["fraud_price_ceiling_factor"],
        )

    # Optionally persist enriched listing
    enriched = {**listing, **result}
    save_listing(enriched)

    return result
