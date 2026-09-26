from typing import Optional, List, Dict
from dealr.config import get_settings
from dealr.core.errors_core import ForbiddenError, NotFoundError
from dealr.data.models_data import VehicleListing, VehicleListingCreate
from dealr.db.collections_db import get_listings_collection


async def get_listing(dealer_id: str, listing_id: str) -> VehicleListing:
    doc = await get_listings_collection().find_one({"listing_id": listing_id})
    if not doc:
        raise NotFoundError(f"Listing '{listing_id}' not found.")
    if doc["dealer_id"] != dealer_id:
        raise ForbiddenError("You do not have access to this listing.")
    return VehicleListing(**{k: v for k, v in doc.items() if k != "_id"})


async def create_listing(dealer_id: str, payload: VehicleListingCreate) -> VehicleListing:
    listing = VehicleListing(dealer_id=dealer_id, **payload.model_dump())
    await get_listings_collection().insert_one(listing.model_dump(mode="json"))
    return listing


class ListingService:
    """
    Core service layer for dealer listings.
    Handles listing creation, retrieval, updates, and deletion.
    """

    def __init__(self):
        self.settings = get_settings()

    # Example: get all listings for a dealer
    async def get_listings(self, dealer_id: str) -> List[Dict]:
        # Replace with real DB lookup
        return [
            {
                "listing_id": "L001",
                "dealer_id": dealer_id,
                "vin": "1HGCM82633A123456",
                "price": 12999,
                "status": "active"
            },
            {
                "listing_id": "L002",
                "dealer_id": dealer_id,
                "vin": "2C4RC1BG7HR123789",
                "price": 18999,
                "status": "pending"
            }
        ]

    # Example: get a single listing
    async def get_listing(self, listing_id: str) -> Optional[Dict]:
        # Replace with real DB lookup
        return {
            "listing_id": listing_id,
            "dealer_id": "123",
            "vin": "1HGCM82633A123456",
            "price": 12999,
            "status": "active"
        }

    # Example: create a listing
    async def create_listing(self, dealer_id: str, data: Dict) -> Dict:
        # Replace with real DB insert
        return {
            "listing_id": "NEW123",
            "dealer_id": dealer_id,
            **data
        }

    # Example: update a listing
    async def update_listing(self, listing_id: str, data: Dict) -> Dict:
        # Replace with real DB update
        return {
            "listing_id": listing_id,
            **data
        }

    # Example: delete a listing
    async def delete_listing(self, listing_id: str) -> bool:
        # Replace with real DB delete
        return True
