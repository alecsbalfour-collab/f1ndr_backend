"""dealr inventory models."""

from typing import ClassVar, FrozenSet, Optional

from pydantic import Field

from api.schemas.list_schemas import VehicleIn, VehicleOut


class InventoryIn(VehicleIn):
    # The owning dealer account is always the authenticated caller.
    server_fields: ClassVar[FrozenSet[str]] = frozenset({"owner_id"})
    name: Optional[str] = Field(None, max_length=200)
    status: Optional[str] = Field(None, max_length=50)


class InventoryItem(VehicleOut):
    id: str
    owner_id: Optional[str] = None
    name: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
