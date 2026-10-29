"""
Repository for dealer inventory.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from db.document_store import DocumentStore

inventory_store = DocumentStore("dealr_inventory", key="id", indexes=("status", "vin", "owner_id", "category", "subcategory"))


async def save_inventory(inv: dict) -> str:
    now = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
    inv.setdefault("id", str(uuid.uuid4()))
    inv.setdefault("status", "active")
    inv["category"] = inv.get("category") or "other"
    inv.setdefault("created_at", now)
    inv["updated_at"] = now
    await inventory_store.upsert(inv)
    return inv["id"]


async def update_inventory_db(inv: dict) -> bool:
    existing = await inventory_store.get(inv["id"]) or {}
    merged = {**existing, **inv, "updated_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat()}
    merged["category"] = merged.get("category") or "other"
    merged.setdefault("created_at", merged["updated_at"])
    return await inventory_store.upsert(merged)


async def get_inventory(inventory_id: str) -> Optional[dict]:
    return await inventory_store.get(inventory_id)


async def list_inventory(
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    owner_id: Optional[str] = None,
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    rv: Optional[dict] = None,
) -> dict:
    query = {
        k: v
        for k, v in {"status": status, "owner_id": owner_id, "category": category, "subcategory": subcategory}.items()
        if v
    }
    if rv:
        from f1ndr.utils.utils import rv_matches
        docs = await inventory_store.find(query, limit=10_000, sort=("created_at", -1))
        docs = [d for d in docs if rv_matches(d, **rv)]
        return {"items": docs[(page - 1) * page_size: page * page_size], "total": len(docs)}
    items = await inventory_store.find(query, skip=(page - 1) * page_size, limit=page_size, sort=("created_at", -1))
    return {"items": items, "total": await inventory_store.count(query)}


async def delete_inventory(inventory_id: str) -> bool:
    return await inventory_store.delete(inventory_id)
