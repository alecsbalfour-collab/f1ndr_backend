from typing import List, Optional

from db.document_store import DocumentStore
from dealr.core.errors_core import ForbiddenError, NotFoundError
from dealr.data.models_data import VehicleListing, VehicleListingCreate, VehicleListingUpdate

listings_store = DocumentStore("listings", key="listing_id", indexes=("dealer_id", "vin", "listing_status"))


async def get_listing(dealer_id: str, listing_id: str) -> VehicleListing:
    doc = await listings_store.get(listing_id)
    if not doc:
        raise NotFoundError(f"Listing '{listing_id}' not found.")
    if doc["dealer_id"] != dealer_id:
        raise ForbiddenError("You do not have access to this listing.")
    return VehicleListing(**doc)


async def create_listing(dealer_id: str, payload: VehicleListingCreate) -> VehicleListing:
    listing = VehicleListing(dealer_id=dealer_id, **payload.model_dump())
    await listings_store.upsert(listing.model_dump(mode="json"))
    return listing


async def list_dealer_listings(dealer_id: str) -> List[VehicleListing]:
    docs = await listings_store.find({"dealer_id": dealer_id}, limit=10_000, sort=("created_at", -1))
    return [VehicleListing(**doc) for doc in docs]


async def update_listing(dealer_id: str, listing_id: str, payload: VehicleListingUpdate) -> VehicleListing:
    listing = await get_listing(dealer_id, listing_id)
    updated = listing.model_copy(update=payload.model_dump(exclude_unset=True))
    await listings_store.upsert(updated.model_dump(mode="json"))
    return updated


async def delete_listing(dealer_id: str, listing_id: str) -> bool:
    await get_listing(dealer_id, listing_id)
    return await listings_store.delete(listing_id)


class ListingService:
    """
    Core service layer for dealer listings.
    Handles listing creation, retrieval, updates, and deletion.
    """

    async def get_listings(self, dealer_id: str) -> List[VehicleListing]:
        return await list_dealer_listings(dealer_id)

    async def get_listing(self, dealer_id: str, listing_id: str) -> VehicleListing:
        return await get_listing(dealer_id, listing_id)

    async def create_listing(self, dealer_id: str, payload: VehicleListingCreate) -> VehicleListing:
        return await create_listing(dealer_id, payload)

    async def update_listing(self, dealer_id: str, listing_id: str, payload: VehicleListingUpdate) -> VehicleListing:
        return await update_listing(dealer_id, listing_id, payload)

    async def delete_listing(self, dealer_id: str, listing_id: str) -> bool:
        return await delete_listing(dealer_id, listing_id)
