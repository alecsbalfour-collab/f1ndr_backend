"""dealr inventory models."""

from typing import Any, ClassVar, Dict, FrozenSet, List, Optional

from pydantic import Field

from api.schemas.common import Record
from api.schemas.list_schemas import Category, VehicleIn, VehicleOut


class InventoryIn(VehicleIn):
    # The owning dealer account is always the authenticated caller.
    server_fields: ClassVar[FrozenSet[str]] = frozenset({"owner_id"})
    name: Optional[str] = Field(None, max_length=200)
    status: Optional[str] = Field(None, max_length=50)


class InventoryCreate(InventoryIn):
    category: Category


class InventoryItem(VehicleOut):
    id: str
    owner_id: Optional[str] = None
    name: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class InventoryPricingRequest(VehicleIn):
    """Vehicle payload the dealer pricing panel estimates comps for."""
    region: Optional[str] = Field(None, max_length=100)


class ComparableOut(Record):
    id: Optional[str] = None
    title: Optional[str] = None
    price: Optional[float] = None
    platform: Optional[str] = None
    region: Optional[str] = None
    url: Optional[str] = None
    mileage: Optional[int] = None
    year: Optional[int] = None


class InventoryPricingOut(Record):
    market_value: Optional[float] = None
    p25: Optional[float] = None
    median: Optional[float] = None
    p75: Optional[float] = None
    suggested_min: Optional[float] = None
    suggested_max: Optional[float] = None
    comp_count: int = 0
    confidence: Optional[str] = None
    book_value: Optional[Dict[str, Any]] = None
    comparables: Optional[List[ComparableOut]] = None
