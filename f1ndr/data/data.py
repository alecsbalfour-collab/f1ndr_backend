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
        "mileage",
        "location",
        "market_value",
    }
    return {k: v for k, v in listing.items() if k in allowed_keys}
