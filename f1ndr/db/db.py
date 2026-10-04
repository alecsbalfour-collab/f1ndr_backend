"""
Database layer for f1ndr.

Listings persist through the shared DocumentStore: Mongo when connected,
in-memory otherwise (tests, dev without Mongo).
"""

import uuid
from typing import Any, Dict, List

from db.document_store import DocumentStore

listings_store = DocumentStore("f1ndr_listings", key="id", indexes=("category", "subcategory", "make"))


async def save_listing(listing: Dict[str, Any]) -> str:
    """Insert or update a listing by its id. Returns the listing id."""
    listing.setdefault("id", str(uuid.uuid4()))
    await listings_store.upsert(listing)
    return listing["id"]


async def query_listings(query: Dict[str, Any] = None, limit: int = 10_000) -> List[Dict[str, Any]]:
    """Listings matching an equality query (all of them by default)."""
    return await listings_store.find(query or {}, limit=limit)


async def count_listings(query: Dict[str, Any] = None) -> int:
    return await listings_store.count(query or {})
