"""
Utility functions for f1ndr.
"""

from typing import Dict, List, Any
import math


def normalize_listing(listing: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize basic fields (strip strings, ensure numeric types).
    """
    out = dict(listing)

    for key in ["title", "description", "make", "model", "location"]:
        if key in out and isinstance(out[key], str):
            out[key] = out[key].strip()

    for key in ["year", "price", "mileage"]:
        if key in out and out[key] is not None:
            try:
                out[key] = int(out[key])
            except (ValueError, TypeError):
                out[key] = None

    return out


def decode_vin(vin: str) -> Dict[str, Any]:
    """
    Very simple VIN decode stub: extracts year and manufacturer hints.
    This is functional and can be replaced with a real API integration.
    """
    vin = vin.strip().upper()
    result: Dict[str, Any] = {"vin": vin}

    if len(vin) == 17:
        year_code = vin[9]
        year_map = {
            "F": 2015,
            "G": 2016,
            "H": 2017,
            "J": 2018,
            "K": 2019,
            "L": 2020,
        }
        if year_code in year_map:
            result["decoded_year"] = year_map[year_code]

        wmi = vin[:3]
        result["wmi"] = wmi

    return result


def compute_market_value(listing: Dict[str, Any]) -> float:
    """
    Compute a simple market value based on year, mileage, and base price.
    """
    base_price = listing.get("price") or 0
    year = listing.get("year") or 0
    mileage = listing.get("mileage") or 0

    if not year or not base_price:
        return float(base_price)

    age = max(0, 2025 - year)
    age_factor = max(0.4, 1.0 - age * 0.03)
    mileage_factor = 1.0 - min(0.5, (mileage / 200_000.0))

    value = base_price * age_factor * mileage_factor
    return round(value, 2)


def _title_similarity(a: str, b: str) -> float:
    """
    Very simple token‑based similarity between two titles.
    """
    a_tokens = set(a.lower().split())
    b_tokens = set(b.lower().split())
    if not a_tokens or not b_tokens:
        return 0.0
    intersection = len(a_tokens & b_tokens)
    union = len(a_tokens | b_tokens)
    return intersection / union


def detect_duplicates(
    listing: Dict[str, Any],
    all_listings: List[Dict[str, Any]],
    title_threshold: float,
    price_delta: float,
) -> List[Dict[str, Any]]:
    """
    Detect potential duplicates based on title similarity and price proximity.
    """
    title = listing.get("title", "")
    price = listing.get("price") or 0
    duplicates: List[Dict[str, Any]] = []

    for other in all_listings:
        if other.get("id") == listing.get("id"):
            continue

        other_title = other.get("title", "")
        other_price = other.get("price") or 0

        sim = _title_similarity(title, other_title)
        if sim < title_threshold:
            continue

        if price == 0 or other_price == 0:
            continue

        delta = abs(price - other_price) / max(price, other_price)
        if delta <= price_delta:
            duplicates.append(other)

    return duplicates


def detect_fraud(
    listing: Dict[str, Any],
    price_floor_factor: float,
    price_ceiling_factor: float,
) -> Dict[str, Any]:
    """
    Simple fraud scoring based on price vs computed market value.
    """
    market_value = compute_market_value(listing)
    price = listing.get("price") or 0

    if market_value <= 0 or price <= 0:
        return {"score": 0.0, "reason": "insufficient_data"}

    ratio = price / market_value
    score = 0.0
    reason = "normal"

    if ratio < price_floor_factor:
        score = min(1.0, (price_floor_factor - ratio) * 2.0)
        reason = "too_cheap_suspicious"
    elif ratio > price_ceiling_factor:
        score = min(1.0, (ratio - price_ceiling_factor) * 2.0)
        reason = "too_expensive_suspicious"

    return {"score": round(score, 2), "reason": reason, "market_value": market_value}
