"""f1ndr models: VIN decode, listing search, intelligence and market value."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, model_validator

from api.schemas.common import VIN, Record
from api.schemas.list_schemas import Category, OptCategory, OptSubcategory, Subcategory, VehicleOut


class VinDecodeRequest(BaseModel):
    vin: VIN


class VinDecodeResult(Record):
    vin: str
    valid: bool
    error: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    manufacturer: Optional[str] = None
    vehicle_type: Optional[str] = None
    body_class: Optional[str] = None
    trim: Optional[str] = None


class SearchRequest(BaseModel):
    category: OptCategory = None
    subcategory: OptSubcategory = None
    make: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    year_min: Optional[int] = Field(None, ge=1886, le=2100)
    year_max: Optional[int] = Field(None, ge=1886, le=2100)
    price_min: Optional[float] = Field(None, ge=0)
    price_max: Optional[float] = Field(None, ge=0)
    text: Optional[str] = Field(None, max_length=200)
    region: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, max_length=200)

    @model_validator(mode="after")
    def _ranges(self) -> "SearchRequest":
        for low, high in (("year_min", "year_max"), ("price_min", "price_max")):
            if getattr(self, low) is not None and getattr(self, high) is not None and getattr(self, low) > getattr(self, high):
                raise ValueError(f"{low} must not exceed {high}")
        return self


class SearchResults(BaseModel):
    results: List[VehicleOut]


class FraudScore(Record):
    score: float
    reason: Optional[str] = None
    market_value: Optional[float] = None


class IntelligenceResult(BaseModel):
    vin: Optional[Dict[str, Any]] = None
    market_value: Optional[float] = None
    duplicates: Optional[List[Dict[str, Any]]] = None
    fraud: Optional[FraudScore] = None


class MarketValue(BaseModel):
    vin: str
    market_value: Optional[float] = None
    confidence: float
    mileage: Optional[int] = None
