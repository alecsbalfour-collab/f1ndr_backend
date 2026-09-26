# scrapers/core/normalization_core.py

import re

_PRICE_PATTERN = re.compile(r"\d[\d,]*(?:\.\d+)?")


def normalize_listing(record: dict) -> dict:
    """
    Normalize basic listing fields.
    """
    normalized = dict(record)

    title = normalized.get("title")
    if isinstance(title, str):
        normalized["title"] = title.strip().title()
    else:
        normalized["title"] = ""

    return normalized


def parse_price(raw: str | None) -> float | None:
    """
    Extract the first numeric amount from a display price.
    "C $12,500.00" -> 12500.0, "$1,200 - $1,500" -> 1200.0, "Free" -> None.
    """
    if not raw:
        return None
    match = _PRICE_PATTERN.search(raw)
    return float(match.group().replace(",", "")) if match else None
