# f1ndr-backend/watchr/core/core.py
"""
Watchr core functions used by other modules.
"""

import logging
import uuid
from datetime import datetime

from db.document_store import DocumentStore
from watchr.data.event_definitions import build_event_payload
from watchr.data.subscription_data import build_subscription_payload


logger = logging.getLogger(__name__)

alerts_store = DocumentStore("watchr_alerts", key="alert_id", indexes=("listing_id", "subscriber"))


async def register_listing_alerts(listing: dict) -> dict:
    event = build_event_payload({
        "event_type": "listing.created",
        "subscriber": listing.get("owner_id") or listing.get("user_id"),
        "listing_id": listing.get("id"),
        "timestamp": datetime.utcnow().isoformat(),
    })
    subscription = {
        **build_subscription_payload(event),
        "alert_id": str(uuid.uuid4()),
        "listing_id": listing.get("id"),
    }
    await alerts_store.upsert(subscription)
    logger.info(f"Registered watchr alerts for listing: {listing.get('id')}")
    return subscription


async def scan_alerts(limit: int = 100) -> list:
    return await alerts_store.find(limit=limit, sort=("timestamp", -1))
