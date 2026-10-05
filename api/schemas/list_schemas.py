"""Vehicle listing fields shared by every module, plus the listr marketplace models."""

from typing import List, Literal, Optional

from pydantic import BaseModel, BeforeValidator, Field, model_validator
from typing_extensions import Annotated

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

# Clients like FlutterFlow send empty strings for unset filters; treat "" as absent.
_BlankToNone = BeforeValidator(lambda v: None if isinstance(v, str) and not v.strip() else v)
OptCategory = Annotated[Optional[Category], _BlankToNone]
OptSubcategory = Annotated[Optional[Subcategory], _BlankToNone]


class VehicleIn(OpenPayload):
    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = Field(None, max_length=10_000)
    vin: Optional[LooseVIN] = None
    category: OptCategory = None
    subcategory: OptSubcategory = None
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
    # Corpus/scrape metadata (present on scraped listings and pushed copies).
    platform: Optional[str] = None
    region: Optional[str] = None
    url: Optional[str] = None
    image: Optional[str] = None
    price_text: Optional[str] = None
    posted: Optional[str] = None
    scraped_at: Optional[str] = None
    first_seen_at: Optional[str] = None


class ComparisonGroup(Record):
    """Listings believed to be the same item across platforms/sellers."""
    key: str
    title: Optional[str] = None
    count: int = 0
    platforms: List[str] = Field(default_factory=list)
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    price_spread: Optional[float] = None
    listings: List[VehicleOut] = Field(default_factory=list)


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
