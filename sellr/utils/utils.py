# f1ndr-backend/sellr/utils/utils.py
"""
DICT-aligned sellr utilities with enterprise features and real database operations.
"""

import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from db.document_store import DocumentStore


logger = logging.getLogger(__name__)

listings_store = DocumentStore("sellr_listings", key="id", indexes=("user_id", "status", "platform", "category", "subcategory"))


async def save_listing(listing: Dict[str, Any]) -> str:
    """Save listing with enterprise metadata. Returns the listing ID."""
    now = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
    listing_id = listing.get("id") or str(uuid.uuid4())
    listing["category"] = listing.get("category") or "other"
    listing["status"] = listing.get("status") or "active"  # keep the response in step with the stored doc
    await listings_store.upsert({
        **listing,
        "id": listing_id,
        "created_at": now,
        "updated_at": now,
        "status": listing.get("status", "active"),
    })
    logger.info(f"Listing saved with ID: {listing_id}")
    return listing_id


async def update_listing(listing_id: str, listing_data: Dict[str, Any]) -> bool:
    """Merge updates into an existing listing. Returns False if it does not exist."""
    existing = await listings_store.get(listing_id)
    if existing is None:
        logger.warning(f"Listing not found for update: {listing_id}")
        return False
    merged = {
        **existing,
        **listing_data,
        "id": listing_id,
        "created_at": existing.get("created_at"),
        "updated_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
    }
    merged["category"] = merged.get("category") or "other"
    await listings_store.upsert(merged)
    logger.info(f"Listing updated: {listing_id}")
    return True


async def delete_listing(listing_id: str) -> bool:
    """Delete listing. Returns False if it did not exist."""
    deleted = await listings_store.delete(listing_id)
    logger.info(f"Listing delete {listing_id}: {deleted}")
    return deleted


async def get_listing(listing_id: str) -> Optional[Dict[str, Any]]:
    """Get listing by ID, or None if not found."""
    return await listings_store.get(listing_id)


async def list_listings(
    filters: Optional[Dict[str, Any]] = None,
    page: int = 1,
    page_size: int = 20,
    rv: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Paginated listing query with equality filters (None values ignored).
    `rv` carries RV attribute filters applied post-query (range/exact mixes)."""
    from f1ndr.utils.utils import rv_matches

    query = {k: v for k, v in (filters or {}).items() if v is not None}
    if rv:
        docs = await listings_store.find(query, limit=10_000, sort=("created_at", -1))
        docs = [d for d in docs if rv_matches(d, **rv)]
        return {"listings": docs[(page - 1) * page_size: page * page_size],
                "total": len(docs), "page": page, "page_size": page_size}
    results = await listings_store.find(query, skip=(page - 1) * page_size, limit=page_size, sort=("created_at", -1))
    total = await listings_store.count(query)
    return {"listings": results, "total": total, "page": page, "page_size": page_size}


async def get_user_listings(
    user_id: str,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
) -> Dict[str, Any]:
    """Get a user's listings with pagination and optional status filter."""
    return await list_listings({"user_id": user_id, "status": status}, page, page_size)
