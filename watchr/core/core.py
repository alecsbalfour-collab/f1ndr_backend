# f1ndr-backend/watchr/core/core.py
"""
Watchr core functions used by other modules.
"""

import logging
from datetime import datetime
from threading import RLock

from watchr.data.event_definitions import build_event_payload
from watchr.data.subscription_data import build_subscription_payload


logger = logging.getLogger(__name__)

_ALERTS: list = []
_LOCK = RLock()


def register_listing_alerts(listing: dict) -> dict:
    event = build_event_payload({
        "event_type": "listing.created",
        "subscriber": listing.get("owner_id") or listing.get("user_id"),
        "listing_id": listing.get("id"),
        "timestamp": datetime.utcnow().isoformat(),
    })
    subscription = build_subscription_payload(event)
    with _LOCK:
        _ALERTS.append(subscription)
    logger.info(f"Registered watchr alerts for listing: {listing.get('id')}")
    return subscription


def scan_alerts() -> list:
    with _LOCK:
        return list(_ALERTS)
