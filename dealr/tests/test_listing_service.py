"""Tests for dealr.core.listing_service_core — CRUD and ownership enforcement."""

from unittest.mock import AsyncMock, patch

import pytest

from dealr.data.models_data import VehicleListingCreate


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
    @pytest.mark.anyio
    async def test_owner_can_get_listing(self) -> None:
        from dealr.core.listing_service_core import get_listing

        mock_col = AsyncMock()
        mock_col.find_one = AsyncMock(return_value=_BASE_LISTING)

        with patch("dealr.core.listing_service_core.get_listings_collection", return_value=mock_col):
            listing = await get_listing(DEALER_A, "listing-001")
            assert listing.listing_id == "listing-001"

    @pytest.mark.anyio
    async def test_non_owner_is_forbidden(self) -> None:
        from dealr.core.errors_core import ForbiddenError
        from dealr.core.listing_service_core import get_listing

        mock_col = AsyncMock()
        mock_col.find_one = AsyncMock(return_value=_BASE_LISTING)

        with patch("dealr.core.listing_service_core.get_listings_collection", return_value=mock_col):
            with pytest.raises(ForbiddenError):
                await get_listing(DEALER_B, "listing-001")

    @pytest.mark.anyio
    async def test_not_found_raises_error(self) -> None:
        from dealr.core.errors_core import NotFoundError
        from dealr.core.listing_service_core import get_listing

        mock_col = AsyncMock()
        mock_col.find_one = AsyncMock(return_value=None)

        with patch("dealr.core.listing_service_core.get_listings_collection", return_value=mock_col):
            with pytest.raises(NotFoundError):
                await get_listing(DEALER_A, "nonexistent-id")


class TestCreateListing:
    @pytest.mark.anyio
    async def test_creates_with_correct_dealer(self) -> None:
        from dealr.core.listing_service_core import create_listing

        payload = VehicleListingCreate(
            vin="1HGCM82633A004352",
            year=2003,
            make="Honda",
            model="Accord",
        )
        mock_col = AsyncMock()
        mock_col.insert_one = AsyncMock()

        with patch("dealr.core.listing_service_core.get_listings_collection", return_value=mock_col):
            listing = await create_listing(DEALER_A, payload)
            assert listing.dealer_id == DEALER_A
            assert listing.vin == "1HGCM82633A004352"
            mock_col.insert_one.assert_called_once()
