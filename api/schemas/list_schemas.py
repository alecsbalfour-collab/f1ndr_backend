"""Vehicle listing fields shared by every module, plus the listr marketplace models."""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field, model_validator

from api.schemas.common import LooseVIN, OpenPayload, Record
from listr.config.config import get_listr_config

ListrPlatform = Literal[tuple(get_listr_config()["supported_platforms"])]

# Classifieds verticals; listings are more than vehicles.
Category = Literal[
    "vehicles", "real_estate", "goods", "services", "jobs", "pets", "community", "other",
]
# Kinds within a vertical. Only vehicles are defined so far; other verticals use "other".
Subcategory = Literal[
    "car", "truck", "motorcycle",
    "motorhome_a", "motorhome_b", "motorhome_c",
    "travel_trailer", "fifth_wheel", "toy_hauler", "truck_camper",
    "other",
]


class VehicleIn(OpenPayload):
    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = Field(None, max_length=10_000)
    vin: Optional[LooseVIN] = None
    category: Optional[Category] = None
    subcategory: Optional[Subcategory] = None
    make: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    trim: Optional[str] = Field(None, max_length=100)
    year: Optional[int] = Field(None, ge=1886, le=2100)
    price: Optional[float] = Field(None, ge=0)
    mileage: Optional[int] = Field(None, ge=0)
    location: Optional[str] = Field(None, max_length=200)

    @model_validator(mode="after")
    def _subcategory_belongs_to_category(self) -> "VehicleIn":
        # Only vehicles have defined subcategories; "other" is valid for any vertical.
        # A missing category means a partial update, where the stored doc decides.
        if self.subcategory not in (None, "other") and self.category not in (None, "vehicles"):
            raise ValueError(f"subcategory '{self.subcategory}' requires category 'vehicles'")
        return self


class VehicleOut(Record):
    # No constraints on output: documents written before validation existed must still load.
    id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    vin: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
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


class ListrListingIn(VehicleIn):
    # Pushing a listing to a marketplace requires knowing what it is.
    category: Category


class ListrResult(BaseModel):
    platform: str
    status: Literal["pushed", "updated", "created"]
    listing: ListrListing


class PlatformList(BaseModel):
    platforms: List[str]
    count: int
