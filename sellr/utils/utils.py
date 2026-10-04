# f1ndr-backend/sellr/utils/utils.py
"""
DICT-aligned sellr utilities with enterprise features and real database operations.
"""

import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from db.document_store import DocumentStore


logger = logging.getLogger(__name__)

listings_store = DocumentStore("sellr_listings", key="id", indexes=("user_id", "status", "platform", "category"))


async def save_listing(listing: Dict[str, Any]) -> str:
    """Save listing with enterprise metadata. Returns the listing ID."""
    now = datetime.utcnow().isoformat()
    listing_id = listing.get("id") or str(uuid.uuid4())
    listing["category"] = listing.get("category") or "car"
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
        "updated_at": datetime.utcnow().isoformat(),
    }
    merged["category"] = merged.get("category") or "car"
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
) -> Dict[str, Any]:
    """Paginated listing query with equality filters (None values ignored)."""
    query = {k: v for k, v in (filters or {}).items() if v is not None}
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
