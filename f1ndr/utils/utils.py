"""
Utility functions for f1ndr.
"""

import hashlib
import re
from typing import Dict, List, Any, Optional
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


def compute_market_value(listing: Dict[str, Any]) -> Optional[float]:
    """
    No pricing provider yet (Pricing roadmap item); None means unknown,
    so callers must not present it as a real value.
    """
    return None


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


_TITLE_STOPWORDS = {
    "for", "sale", "the", "a", "an", "in", "on", "obo", "firm", "new", "used",
    "great", "good", "excellent", "condition", "mint", "must", "go", "price",
    "reduced", "selling", "moving", "pickup", "only",
}


def _title_tokens(title: str) -> set:
    """Normalized content tokens: lowercase alphanumeric, filler words dropped."""
    return {t for t in re.findall(r"[a-z0-9]+", (title or "").lower()) if t not in _TITLE_STOPWORDS}


def _same_when_present(a: dict, b: dict, fields) -> bool:
    """Structured fields must agree whenever both listings carry a value."""
    for f in fields:
        av, bv = a.get(f), b.get(f)
        if av is not None and bv is not None and str(av).strip().lower() != str(bv).strip().lower():
            return False
    return True


def listings_equivalent(a: dict, b: dict, title_threshold: float = 0.6, price_delta: float = 0.15) -> bool:
    """Are two listings likely the same item on different platforms?

    General-classifieds rules (not vehicle-specific): same category and region,
    shared structured fields must agree when both are set, titles must be similar
    enough, and prices must be within the delta when both have one.
    """
    if a is b or (a.get("id") and a.get("id") == b.get("id")):
        return False
    if (a.get("category") or "other") != (b.get("category") or "other"):
        return False
    if a.get("region") and b.get("region") and a["region"] != b["region"]:
        return False
    if not _same_when_present(a, b, ("year", "make", "model")):
        return False
    ta, tb = _title_tokens(a.get("title", "")), _title_tokens(b.get("title", ""))
    if not ta or not tb:
        return False
    if len(ta & tb) / len(ta | tb) < title_threshold:
        return False
    pa, pb = a.get("price"), b.get("price")
    if (
        isinstance(pa, (int, float))
        and isinstance(pb, (int, float))
        and max(pa, pb) > 0
        and abs(pa - pb) / max(pa, pb) > price_delta
    ):
        return False
    return True


def group_equivalent_listings(
    listings: List[dict],
    title_threshold: float = 0.6,
    price_delta: float = 0.15,
) -> List[dict]:
    """Cluster listings into comparison groups (size >= 2) via union-find.

    Pairwise checks are bucketed by (category, region) to keep the cost sane as
    the corpus grows; refine with a blocking index if buckets get big.
    Each group: key, title, count, platforms, min/max price, spread, listings.
    """
    n = len(listings)
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x: int, y: int) -> None:
        parent[find(x)] = find(y)

    buckets: Dict[Any, List[int]] = {}
    for i, l in enumerate(listings):
        buckets.setdefault((l.get("category") or "other", l.get("region")), []).append(i)

    for bucket in buckets.values():
        for pos in range(len(bucket)):
            for other in bucket[pos + 1:]:
                if listings_equivalent(
                    listings[bucket[pos]], listings[other], title_threshold, price_delta
                ):
                    union(bucket[pos], other)

    clusters: Dict[int, List[dict]] = {}
    for i, l in enumerate(listings):
        clusters.setdefault(find(i), []).append(l)

    groups = []
    for members in clusters.values():
        if len(members) < 2:
            continue
        members.sort(key=lambda d: (d.get("price") is None, d.get("price") or 0))
        prices = [d["price"] for d in members if isinstance(d.get("price"), (int, float))]
        key = hashlib.sha256(
            "|".join(sorted(d.get("id") or d.get("url") or "" for d in members)).encode()
        ).hexdigest()[:12]
        groups.append(
            {
                "key": key,
                "title": members[0].get("title"),
                "count": len(members),
                "platforms": sorted({d.get("platform") for d in members if d.get("platform")}),
                "min_price": min(prices) if prices else None,
                "max_price": max(prices) if prices else None,
                "price_spread": (max(prices) - min(prices)) if prices else None,
                "listings": members,
            }
        )
    groups.sort(key=lambda g: (-g["count"], g["min_price"] if g["min_price"] is not None else 0))
    return groups


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

    if market_value is None or market_value <= 0 or price <= 0:
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
