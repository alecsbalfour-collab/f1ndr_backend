# f1ndr-backend/watchr/core/core.py
"""
Watchr core functions used by other modules and the API routes.
"""

import logging
import uuid
from datetime import datetime
from typing import Optional

from db.document_store import DocumentStore
from watchr.data.event_definitions import build_event_payload
from watchr.data.subscription_data import build_subscription_payload


logger = logging.getLogger(__name__)

alerts_store = DocumentStore("watchr_alerts", key="alert_id", indexes=("listing_id", "subscriber", "user_id"))
subscriptions_store = DocumentStore("watchr_subscriptions", key="subscription_id", indexes=("user_id",))


def _timestamps() -> dict:
    now = datetime.utcnow().isoformat()
    return {"created_at": now, "updated_at": now}


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


async def create_alert(data: dict) -> dict:
    """Persist a saved-search alert for a user."""
    alert = {**data, "alert_id": str(uuid.uuid4()), "status": data.get("status", "active"), **_timestamps()}
    await alerts_store.upsert(alert)
    return alert


async def get_alert(alert_id: str) -> Optional[dict]:
    return await alerts_store.get(alert_id)


async def list_alerts(user_id: str, status: Optional[str] = None, page: int = 1, page_size: int = 20) -> dict:
    query = {k: v for k, v in {"user_id": user_id, "status": status}.items() if v}
    alerts = await alerts_store.find(query, skip=(page - 1) * page_size, limit=page_size, sort=("created_at", -1))
    return {"alerts": alerts, "total": await alerts_store.count(query)}


async def delete_alert(alert_id: str) -> bool:
    return await alerts_store.delete(alert_id)


async def create_subscription(data: dict) -> dict:
    """Persist a subscription for a user."""
    subscription = {**data, "subscription_id": str(uuid.uuid4()), **_timestamps()}
    await subscriptions_store.upsert(subscription)
    return subscription


async def get_subscription(subscription_id: str) -> Optional[dict]:
    return await subscriptions_store.get(subscription_id)


async def list_subscriptions(user_id: str, page: int = 1, page_size: int = 20) -> dict:
    query = {"user_id": user_id}
    subs = await subscriptions_store.find(query, skip=(page - 1) * page_size, limit=page_size, sort=("created_at", -1))
    return {"subscriptions": subs, "total": await subscriptions_store.count(query)}


async def delete_subscription(subscription_id: str) -> bool:
    return await subscriptions_store.delete(subscription_id)


async def scan_alerts(limit: int = 100) -> list:
    return await alerts_store.find(limit=limit, sort=("timestamp", -1))
