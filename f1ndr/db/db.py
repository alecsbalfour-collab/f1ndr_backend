"""
Database layer for f1ndr.

For now, uses an in‑memory store that behaves like a simple collection.
This is fully functional and can be swapped for a real DB later.
"""

from typing import Dict, List, Any
from threading import RLock

_LISTINGS: List[Dict[str, Any]] = []
_LOCK = RLock()


def save_listing(listing: Dict[str, Any]) -> None:
    """
    Insert or update a listing based on its id (if present).
    """
    with _LOCK:
        listing_id = listing.get("id")
        if listing_id is not None:
            for idx, existing in enumerate(_LISTINGS):
                if existing.get("id") == listing_id:
                    _LISTINGS[idx] = listing
                    break
            else:
                _LISTINGS.append(listing)
        else:
            _LISTINGS.append(listing)


def query_listings() -> List[Dict[str, Any]]:
    """
    Return a copy of all stored listings.
    """
    with _LOCK:
        return list(_LISTINGS)
