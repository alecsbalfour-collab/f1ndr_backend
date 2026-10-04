"""
Database layer for f1ndr.

Listings persist through the shared DocumentStore: Mongo when connected,
in-memory otherwise (tests, dev without Mongo).
"""

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from db.document_store import DocumentStore

listings_store = DocumentStore(
    "f1ndr_listings",
    key="id",
    indexes=("category", "subcategory", "make", "platform", "region"),
)


async def save_listing(listing: Dict[str, Any]) -> str:
    """Insert or update a listing by its id. Returns the listing id."""
    listing.setdefault("id", str(uuid.uuid4()))
    await listings_store.upsert(listing)
    return listing["id"]


def scraped_listing_id(platform: str, url: str) -> str:
    """Stable id from the listing URL: re-scraping refreshes one doc instead of duplicating."""
    return f"{platform}:{hashlib.sha256(url.encode()).hexdigest()[:16]}"


async def save_scraped_listings(
    listings: List[Dict[str, Any]],
    platform: str,
    category: str = "other",
    region: str = "calgary",
) -> int:
    """Upsert a scraper's results into the f1ndr corpus.

    `price` stays numeric (from the parsed price_value); the site's display string is
    kept as `price_text`. `first_seen_at` survives refreshes; `scraped_at` moves.
    """
    now = datetime.now(timezone.utc).isoformat()
    saved = 0
    for raw in listings:
        url, title = raw.get("url"), raw.get("title")
        if not url or not title:
            continue
        price = raw.get("price_value")
        doc = {
            **raw,
            "id": scraped_listing_id(platform, url),
            "platform": platform,
            "price": price if isinstance(price, (int, float)) else None,
            "price_text": raw.get("price") if isinstance(raw.get("price"), str) else None,
            "category": raw.get("category") or category,
            "region": raw.get("region") or region,
            "scraped_at": now,
        }
        existing = await listings_store.get(doc["id"])
        doc["first_seen_at"] = (existing or {}).get("first_seen_at") or now
        await listings_store.upsert(doc)
        saved += 1
    return saved


async def query_listings(query: Dict[str, Any] = None, limit: int = 10_000) -> List[Dict[str, Any]]:
    """Listings matching an equality query (all of them by default)."""
    return await listings_store.find(query or {}, limit=limit)


async def count_listings(query: Dict[str, Any] = None) -> int:
    return await listings_store.count(query or {})
