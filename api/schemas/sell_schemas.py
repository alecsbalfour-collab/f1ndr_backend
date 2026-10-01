"""sellr listing models."""

from typing import ClassVar, FrozenSet, Optional

from pydantic import Field

from api.schemas.list_schemas import VehicleIn, VehicleOut


class SellListingUpdate(VehicleIn):
    # The seller is always the authenticated caller.
    server_fields: ClassVar[FrozenSet[str]] = frozenset({"user_id"})
    status: Optional[str] = Field(None, max_length=50)
    platform: Optional[str] = Field(None, max_length=50)


class SellListingCreate(SellListingUpdate):
    title: str = Field(..., min_length=1, max_length=500)
    price: float = Field(..., ge=0)


class SellListing(VehicleOut):
    id: str
    user_id: Optional[str] = None
    status: Optional[str] = None
    platform: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
