"""
Market value intelligence: local comps from the scraped listing corpus, plus a
config-gated book-value provider hook (P3 — Canadian Black Book / J.D. Power).
"""

import os
import statistics
from typing import Any, Dict, List, Optional

from f1ndr.utils.utils import _title_tokens


def compute_market_value(data: dict) -> Optional[float]:
    """Legacy sync stub kept for callers that predate estimate_market_price.
    None means unknown, not zero."""
    return None


def _comp_ok(listing: dict, comp: dict) -> bool:
    """Does `comp` qualify as a comparable for `listing`?"""
    if comp.get("id") and comp.get("id") == listing.get("id"):
        return False
    if (comp.get("category") or "other") != (listing.get("category") or "other"):
        return False
    if listing.get("subcategory") and comp.get("subcategory") not in (None, listing["subcategory"]):
        return False
    make, model = (listing.get("make") or "").lower(), (listing.get("model") or "").lower()
    if make and comp.get("make") and comp["make"].lower() != make:
        return False
    if model and comp.get("model") and comp["model"].lower() != model:
        return False
    # Scraped docs often lack make/model — fall back to title-token overlap.
    if (make or model) and not (comp.get("make") or comp.get("model")):
        mine = _title_tokens(listing.get("title", ""))
        theirs = _title_tokens(comp.get("title", ""))
        if not mine or not theirs or len(mine & theirs) / len(mine | theirs) < 0.3:
            return False
    year = listing.get("year")
    if year and comp.get("year") and abs(comp["year"] - year) > 2:
        return False
    mileage = listing.get("mileage")
    if mileage is not None and comp.get("mileage") is not None and abs(comp["mileage"] - mileage) > 40_000:
        return False
    return True


def _book_value(listing: dict) -> Optional[Dict[str, Any]]:
    """P3 hook: only active when ENABLE_BOOK_VALUES + a provider key are set.
    Real provider calls land later; for now the shape is reserved."""
    if os.getenv("ENABLE_BOOK_VALUES", "false").lower() != "true":
        return None
    provider = ("canadian_black_book" if os.getenv("CBB_API_KEY")
                else "jd_power" if os.getenv("JDPOWER_API_KEY") else None)
    if not provider:
        return None
    return {"provider": provider, "value": None, "note": "provider integration pending"}


async def estimate_market_price(listing: dict, corpus: Optional[List[dict]] = None) -> Dict[str, Any]:
    """Estimate asking-price comps for a listing from the corpus.

    Comps: same category (+subcategory when set), make/model agree when both
    sides carry them (title-token fallback otherwise), +/-2 years, +/-40,000 km,
    same region preferred. Percentiles are local asking prices, not sold prices.
    """
    if corpus is None:
        from f1ndr.core.core import query_listings  # lazy: avoids the module cycle
        corpus = await query_listings({})

    ok_comps = [c for c in corpus if _comp_ok(listing, c)]
    region = listing.get("region")
    same_region = [c for c in ok_comps if c.get("region") == region] if region else []
    comps = same_region if len(same_region) >= 3 else ok_comps

    prices = sorted(c["price"] for c in comps
                    if isinstance(c.get("price"), (int, float)) and c["price"] > 0)
    out: Dict[str, Any] = {
        "market_value": None, "p25": None, "median": None, "p75": None,
        "suggested_min": None, "suggested_max": None,
        "comp_count": len(prices), "confidence": "none",
        "provider": "local_comps", "comparables": [], "book_value": _book_value(listing),
    }
    if not prices:
        return out

    med = statistics.median(prices)
    if len(prices) >= 2:
        q = statistics.quantiles(prices, n=4)
        p25, p75 = q[0], q[2]
    else:
        p25 = p75 = prices[0]
    out.update(
        market_value=med, median=med, p25=p25, p75=p75,
        suggested_min=p25, suggested_max=p75,
        confidence="high" if len(prices) >= 10 else "medium" if len(prices) >= 4 else "low",
        comparables=[{"id": c.get("id"), "title": c.get("title"), "price": c.get("price"),
                      "platform": c.get("platform"), "region": c.get("region"),
                      "url": c.get("url"), "mileage": c.get("mileage"), "year": c.get("year")}
                     for c in comps[:10]],
    )
    return out
