"""
Data helpers for f1ndr.
"""

from typing import Any, Dict


def serialize_listing(listing: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure listing is JSON‑serializable and only contains expected keys.
    """
    allowed_keys = {
        "id",
        "vin",
        "category",
        "subcategory",
        "title",
        "description",
        "make",
        "model",
        "year",
        "price",
        "price_text",
        "mileage",
        "location",
        "region",
        "platform",
        "url",
        "image",
        "posted",
        "details",
        "scraped_at",
        "first_seen_at",
        "market_value",
        "length_ft",
        "dry_weight_lbs",
        "gvwr_lbs",
        "sleeps",
        "slide_outs",
        "hitch_type",
        "fresh_water_gal",
        "grey_water_gal",
        "black_water_gal",
        "engine",
        "chassis",
    }
    return {k: v for k, v in listing.items() if k in allowed_keys}
