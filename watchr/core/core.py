# f1ndr-backend/watchr/core/core.py
"""
Watchr core functions used by other modules and the API routes.
"""

import logging
import uuid
from datetime import datetime
from typing import List, Optional

from db.document_store import DocumentStore
from watchr.data.event_definitions import build_event_payload
from watchr.data.subscription_data import build_subscription_payload


logger = logging.getLogger(__name__)

alerts_store = DocumentStore("watchr_alerts", key="alert_id", indexes=("listing_id", "subscriber", "user_id"))
subscriptions_store = DocumentStore("watchr_subscriptions", key="subscription_id", indexes=("user_id",))
matches_store = DocumentStore("watchr_matches", key="id", indexes=("user_id", "alert_id", "listing_id"))


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


def _alert_matches(alert: dict, listing: dict) -> bool:
    """Does a persisted listing satisfy an alert's saved-search filters?

    Only explicit "active" alerts match (legacy listing-subscription records lack a
    status and must never spam). Missing listing fields don't exclude it — scraped
    docs rarely carry year/make/model — except that a set make/model must appear
    either as an exact field match or in the listing's text.
    """
    if alert.get("status") != "active":
        return False

    # An alert with no filters would match everything — treat it as not yet configured.
    _FILTERS = ("query", "category", "subcategory", "make", "model",
                "year_min", "year_max", "price_min", "price_max", "region", "location")
    if not any(alert.get(k) not in (None, "") for k in _FILTERS):
        return False

    blob = " ".join(
        str(listing.get(k) or "") for k in ("title", "description", "make", "model", "location")
    ).lower()

    if alert.get("category") and (listing.get("category") or "other") != alert["category"]:
        return False
    if alert.get("subcategory") and (listing.get("subcategory") or "other") != alert["subcategory"]:
        return False
    if alert.get("region") and (listing.get("region") or "") != alert["region"]:
        return False
    if alert.get("location") and alert["location"].lower() not in blob:
        return False
    for key in ("make", "model"):
        wanted = alert.get(key)
        if wanted and listing.get(key) != wanted and wanted.lower() not in blob:
            return False
    year = listing.get("year")
    if alert.get("year_min") and year and year < alert["year_min"]:
        return False
    if alert.get("year_max") and year and year > alert["year_max"]:
        return False
    price = listing.get("price")
    if alert.get("price_min") and price and price < alert["price_min"]:
        return False
    if alert.get("price_max") and price and price > alert["price_max"]:
        return False
    query = (alert.get("query") or "").strip().lower()
    if query and query not in blob:
        return False
    return True


async def evaluate_listing(listing: dict) -> int:
    """Match one listing against active alerts; email the owner on first match.

    A `watchr_matches` record per (alert, listing) dedupes re-scrapes and feeds
    `GET /watchr/matches`. Returns the number of new matches.
    """
    from api.auth.accounts import get_user
    from api.auth.email import send_email

    if not listing.get("id"):
        return 0
    matched = 0
    for alert in await alerts_store.find({"status": "active"}, limit=10_000):
        if not _alert_matches(alert, listing):
            continue
        match_id = f"{alert['alert_id']}:{listing['id']}"
        if await matches_store.get(match_id):
            continue
        record = {
            "id": match_id,
            "alert_id": alert["alert_id"],
            "alert_name": alert.get("name"),
            "user_id": alert.get("user_id"),
            "listing_id": listing["id"],
            "listing": {
                k: listing.get(k)
                for k in ("title", "price", "price_text", "url", "image", "platform", "location", "region")
            },
            "matched_at": datetime.utcnow().isoformat(),
            "notified": False,
        }
        await matches_store.upsert(record)

        user = await get_user(alert.get("user_id") or "")
        if user and user.get("email"):
            sent = await send_email(
                user["email"],
                f"f1ndr alert: {listing.get('title') or 'new match'}",
                f'Your alert "{alert.get("name")}" matched a new listing.\n\n'
                f"{listing.get('title')}\n"
                f"Price: {listing.get('price_text') or listing.get('price') or 'n/a'}\n"
                f"Location: {listing.get('location') or 'n/a'}\n"
                f"Source: {listing.get('platform') or 'n/a'}\n\n"
                f"{listing.get('url') or ''}",
            )
            if sent:
                await matches_store.update(match_id, {"notified": True})
        matched += 1
    return matched


async def evaluate_listings(listings: List[dict]) -> int:
    """Evaluate a batch; one bad listing must not stop the rest of ingest."""
    matched = 0
    for listing in listings:
        try:
            matched += await evaluate_listing(listing)
        except Exception:
            logger.exception("watchr: failed to evaluate listing %s", listing.get("id"))
    return matched


async def list_matches(user_id: str, page: int = 1, page_size: int = 20) -> dict:
    query = {"user_id": user_id}
    matches = await matches_store.find(query, skip=(page - 1) * page_size, limit=page_size, sort=("matched_at", -1))
    return {"matches": matches, "total": await matches_store.count(query)}
