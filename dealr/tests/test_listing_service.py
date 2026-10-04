"""Tests for dealr.core.listing_service_core — CRUD and ownership enforcement.

Uses the shared DocumentStore in-memory fallback (no Mongo needed).
"""

import pytest

from dealr.core.errors_core import ForbiddenError, NotFoundError
from dealr.core.listing_service_core import (
    create_listing,
    delete_listing,
    get_listing,
    listings_store,
    list_dealer_listings,
    update_listing,
)
from dealr.data.models_data import VehicleListingCreate, VehicleListingUpdate


DEALER_A = "dealer-aaa-111"
DEALER_B = "dealer-bbb-222"

_BASE_LISTING = {
    "listing_id":     "listing-001",
    "dealer_id":      DEALER_A,
    "vin":            "1HGCM82633A004352",
    "year":           2003,
    "make":           "Honda",
    "model":          "Accord",
    "listing_status": "draft",
    "publish_state":  "hidden",
    "mismatch_flags": [],
    "extra":          {},
    "created_at":     "2026-01-01T00:00:00+00:00",
    "updated_at":     "2026-01-01T00:00:00+00:00",
}


class TestGetListing:
    async def test_owner_can_get_listing(self) -> None:
        await listings_store.upsert(dict(_BASE_LISTING))
        listing = await get_listing(DEALER_A, "listing-001")
        assert listing.listing_id == "listing-001"

    async def test_non_owner_is_forbidden(self) -> None:
        await listings_store.upsert(dict(_BASE_LISTING))
        with pytest.raises(ForbiddenError):
            await get_listing(DEALER_B, "listing-001")

    async def test_not_found_raises_error(self) -> None:
        with pytest.raises(NotFoundError):
            await get_listing(DEALER_A, "nonexistent-id")


class TestCreateListing:
    async def test_creates_with_correct_dealer(self) -> None:
        payload = VehicleListingCreate(
            vin="1HGCM82633A004352",
            year=2003,
            make="Honda",
            model="Accord",
        )
        listing = await create_listing(DEALER_A, payload)
        assert listing.dealer_id == DEALER_A
        assert listing.vin == "1HGCM82633A004352"
        assert await listings_store.get(listing.listing_id) is not None


class TestUpdateDeleteList:
    async def test_list_returns_only_dealers_listings(self) -> None:
        await listings_store.upsert(dict(_BASE_LISTING))
        await listings_store.upsert({**_BASE_LISTING, "listing_id": "listing-002", "dealer_id": DEALER_B})
        ids = {l.listing_id for l in await list_dealer_listings(DEALER_A)}
        assert "listing-001" in ids and "listing-002" not in ids

    async def test_update_changes_fields(self) -> None:
        await listings_store.upsert(dict(_BASE_LISTING))
        updated = await update_listing(DEALER_A, "listing-001", VehicleListingUpdate(price_cad=12995))
        assert updated.price_cad == 12995
        assert (await listings_store.get("listing-001"))["price_cad"] == 12995

    async def test_non_owner_cannot_update(self) -> None:
        await listings_store.upsert(dict(_BASE_LISTING))
        with pytest.raises(ForbiddenError):
            await update_listing(DEALER_B, "listing-001", VehicleListingUpdate(price_cad=12995))

    async def test_delete_removes_listing(self) -> None:
        await listings_store.upsert(dict(_BASE_LISTING))
        assert await delete_listing(DEALER_A, "listing-001") is True
        assert await listings_store.get("listing-001") is None

    async def test_non_owner_cannot_delete(self) -> None:
        await listings_store.upsert(dict(_BASE_LISTING))
        with pytest.raises(ForbiddenError):
            await delete_listing(DEALER_B, "listing-001")
