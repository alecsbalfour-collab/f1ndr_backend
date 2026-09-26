"""
Repository for marketplace listings, keyed by platform + listing id.
"""

import uuid

from db.document_store import DocumentStore

listings_store = DocumentStore("listr_listings", key="key", indexes=("platform", "id"))


def _keyed(platform: str, listing: dict) -> dict:
    listing.setdefault("id", str(uuid.uuid4()))
    return {**listing, "key": f"{platform}:{listing['id']}"}


async def save_listing(platform: str, listing: dict):
    await listings_store.upsert(_keyed(platform, listing))
    return True


async def update_listing_db(platform: str, listing: dict):
    return await listings_store.upsert(_keyed(platform, listing))


async def remove_listing_db(platform: str, listing: dict):
    return await listings_store.delete(f"{platform}:{listing.get('id')}")
