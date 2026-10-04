"""Vehicle listing fields shared by every module, plus the listr marketplace models."""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from api.schemas.common import LooseVIN, OpenPayload, Record
from listr.config.config import get_listr_config

ListrPlatform = Literal[tuple(get_listr_config()["supported_platforms"])]

VehicleCategory = Literal[
    "car", "truck", "motorcycle",
    "motorhome_a", "motorhome_b", "motorhome_c",
    "travel_trailer", "fifth_wheel", "toy_hauler", "truck_camper",
    "other",
]
# Documents written before `category` existed (and payloads that omit it) are cars.
DEFAULT_CATEGORY = "car"


class VehicleIn(OpenPayload):
    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = Field(None, max_length=10_000)
    vin: Optional[LooseVIN] = None
    category: Optional[VehicleCategory] = None
    make: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    trim: Optional[str] = Field(None, max_length=100)
    year: Optional[int] = Field(None, ge=1886, le=2100)
    price: Optional[float] = Field(None, ge=0)
    mileage: Optional[int] = Field(None, ge=0)
    location: Optional[str] = Field(None, max_length=200)


class VehicleOut(Record):
    # No constraints on output: documents written before validation existed must still load.
    id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    vin: Optional[str] = None
    category: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    trim: Optional[str] = None
    year: Optional[int] = None
    price: Optional[float] = None
    mileage: Optional[int] = None
    location: Optional[str] = None
    market_value: Optional[float] = None


class ListrListing(VehicleOut):
    platform: str
    updated_at: str


class ListrResult(BaseModel):
    platform: str
    status: Literal["pushed", "updated", "created"]
    listing: ListrListing


class PlatformList(BaseModel):
    platforms: List[str]
    count: int
