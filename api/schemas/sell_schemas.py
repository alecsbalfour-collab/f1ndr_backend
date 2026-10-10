"""sellr listing models."""

from typing import ClassVar, FrozenSet, List, Optional

from pydantic import BaseModel, Field

from api.schemas.common import Record
from api.schemas.list_schemas import Category, VehicleIn, VehicleOut


class SellListingUpdate(VehicleIn):
    # The seller is always the authenticated caller.
    server_fields: ClassVar[FrozenSet[str]] = frozenset({"user_id"})
    status: Optional[str] = Field(None, max_length=50)
    platform: Optional[str] = Field(None, max_length=50)


class SellListingCreate(SellListingUpdate):
    title: str = Field(..., min_length=1, max_length=500)
    price: float = Field(..., ge=0)
    category: Category


class SellListing(VehicleOut):
    id: str
    user_id: Optional[str] = None
    status: Optional[str] = None
    platform: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class PhotoSessionCreate(BaseModel):
    """Optional body for creating a send-to-phone photo session."""
    listing_id: Optional[str] = Field(None, max_length=100)


class PhotoSessionCreated(Record):
    """Returned once, when the session is created; the token lives inside phone_url."""
    session_id: str
    phone_url: str
    status: str
    expires_at: str


class PhotoOut(Record):
    """Public metadata for one uploaded photo (never carries bytes or token material)."""
    id: str
    content_type: Optional[str] = None
    size: Optional[int] = None
    created_at: Optional[str] = None
    url: Optional[str] = None


class PhotoSessionOut(Record):
    id: str
    status: str
    photos: List[PhotoOut] = []
    listing_id: Optional[str] = None
    created_at: Optional[str] = None
    expires_at: Optional[str] = None


class PhotoContent(Record):
    """Owner-only photo fetch: bytes are base64 so the envelope stays typed JSON."""
    id: str
    content_type: str
    size: int
    data_b64: str
