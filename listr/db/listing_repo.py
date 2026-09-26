"""
Repository for marketplace listings.

In-memory store keyed by (platform, listing id); swap for Mongo later.
"""

import uuid
from threading import RLock

_LISTINGS: dict = {}
_LOCK = RLock()


def save_listing(platform: str, listing: dict):
    with _LOCK:
        listing.setdefault("id", str(uuid.uuid4()))
        _LISTINGS[(platform, listing["id"])] = listing
    return True


def update_listing_db(platform: str, listing: dict):
    with _LOCK:
        existed = (platform, listing.get("id")) in _LISTINGS
        save_listing(platform, listing)
    return existed


def remove_listing_db(platform: str, listing: dict):
    with _LOCK:
        return _LISTINGS.pop((platform, listing.get("id")), None) is not None
