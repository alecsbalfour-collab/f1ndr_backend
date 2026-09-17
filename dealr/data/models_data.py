"""dealr.data.models_data — All Pydantic domain models and enumerations."""

import re
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# ── Enumerations ─────────────────────────────────────────────────────────────

class ListingStatus(str, Enum):
    draft     = "draft"
    published = "published"
    sold      = "sold"
    archived  = "archived"


class PublishState(str, Enum):
    live   = "live"
    hidden = "hidden"


class JobStatus(str, Enum):
    pending   = "pending"
    running   = "running"
    completed = "completed"
    failed    = "failed"


class DecodeStatus(str, Enum):
    success     = "success"
    invalid_vin = "invalid_vin"
    api_error   = "api_error"
    not_found   = "not_found"


# ── VIN Decode ────────────────────────────────────────────────────────────────

class VinDecodeResult(BaseModel):
    vin:           str
    year:          Optional[str]           = None
    make:          Optional[str]           = None
    model:         Optional[str]           = None
    trim:          Optional[str]           = None
    body_class:    Optional[str]           = None
    engine:        Optional[str]           = None
    transmission:  Optional[str]           = None
    drive_type:    Optional[str]           = None
    plant_country: Optional[str]           = None
    decode_status: DecodeStatus            = DecodeStatus.success
    mismatch_flags: List[str]              = Field(default_factory=list)


class VinBatchDecodeRequest(BaseModel):
    vins: List[str] = Field(..., min_length=1, max_length=500)


class VinBatchItemResult(BaseModel):
    vin:     str
    decoded: Optional[VinDecodeResult] = None
    error:   Optional[str]             = None


class VinBatchDecodeResponse(BaseModel):
    job_id:         str
    dealer_id:      str
    total_vins:     int
    processed_vins: int
    status:         JobStatus
    results:        List[VinBatchItemResult] = Field(default_factory=list)


# ── Dealer ────────────────────────────────────────────────────────────────────

class DealerCreate(BaseModel):
    dealership_name: str  = Field(..., min_length=2, max_length=120)
    email:           str  = Field(..., pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password:        str  = Field(..., min_length=8)
    phone:           Optional[str]       = None
    address:         Optional[str]       = None
    city:            Optional[str]       = None
    province_state:  Optional[str]       = None
    country:         str                 = Field(default="CA")
    staff_roles:     Dict[str, str]      = Field(default_factory=dict)


class DealerUpdate(BaseModel):
    dealership_name: Optional[str]       = None
    phone:           Optional[str]       = None
    address:         Optional[str]       = None
    city:            Optional[str]       = None
    province_state:  Optional[str]       = None
    country:         Optional[str]       = None
    staff_roles:     Optional[Dict[str, str]] = None


class Dealer(BaseModel):
    dealer_id:       str  = Field(default_factory=lambda: str(uuid.uuid4()))
    dealership_name: str
    email:           str
    password_hash:   str
    phone:           Optional[str]       = None
    address:         Optional[str]       = None
    city:            Optional[str]       = None
    province_state:  Optional[str]       = None
    country:         str                 = "CA"
    staff_roles:     Dict[str, str]      = Field(default_factory=dict)
    created_at:      datetime            = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    updated_at:      datetime            = Field(default_factory=lambda: datetime.now(tz=timezone.utc))


class DealerPublic(BaseModel):
    dealer_id:       str
    dealership_name: str
    email:           str
    phone:           Optional[str]       = None
    address:         Optional[str]       = None
    city:            Optional[str]       = None
    province_state:  Optional[str]       = None
    country:         str
    staff_roles:     Dict[str, str]      = Field(default_factory=dict)
    created_at:      datetime
    updated_at:      datetime


# ── Vehicle Listing ───────────────────────────────────────────────────────────

_VIN_RE = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$")


class VehicleListingCreate(BaseModel):
    vin:            str = Field(..., min_length=17, max_length=17)
    year:           int = Field(..., ge=1900, le=2100)
    make:           str = Field(..., min_length=1)
    model:          str = Field(..., min_length=1)
    trim:           Optional[str]        = None
    mileage_km:     Optional[int]        = Field(None, ge=0)
    price_cad:      Optional[float]      = Field(None, ge=0)
    colour_ext:     Optional[str]        = None
    colour_int:     Optional[str]        = None
    description:    Optional[str]        = None
    extra:          Dict[str, Any]       = Field(default_factory=dict)

    @field_validator("vin")
    @classmethod
    def vin_must_be_valid(cls, v: str) -> str:
        normalised = v.upper().strip()
        if not _VIN_RE.match(normalised):
            raise ValueError("VIN must be 17 characters (A-H, J-N, P-Z, 0-9).")
        return normalised


class VehicleListingUpdate(BaseModel):
    year:        Optional[int]   = Field(None, ge=1900, le=2100)
    make:        Optional[str]   = None
    model:       Optional[str]   = None
    trim:        Optional[str]   = None
    mileage_km:  Optional[int]   = Field(None, ge=0)
    price_cad:   Optional[float] = Field(None, ge=0)
    colour_ext:  Optional[str]   = None
    colour_int:  Optional[str]   = None
    description: Optional[str]   = None
    extra:       Optional[Dict[str, Any]] = None


class VehicleListing(BaseModel):
    listing_id:     str       = Field(default_factory=lambda: str(uuid.uuid4()))
    dealer_id:      str
    vin:            str
    year:           int
    make:           str
    model:          str
    trim:           Optional[str]        = None
    mileage_km:     Optional[int]        = None
    price_cad:      Optional[float]      = None
    colour_ext:     Optional[str]        = None
    colour_int:     Optional[str]        = None
    description:    Optional[str]        = None
    extra:          Dict[str, Any]       = Field(default_factory=dict)
    listing_status: ListingStatus        = ListingStatus.draft
    publish_state:  PublishState         = PublishState.hidden
    # VIN decode cache
    decode_status:  Optional[DecodeStatus]    = None
    mismatch_flags: List[str]                 = Field(default_factory=list)
    decoded_year:   Optional[str]             = None
    decoded_make:   Optional[str]             = None
    decoded_model:  Optional[str]             = None
    decoded_trim:   Optional[str]             = None
    created_at:     datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    updated_at:     datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))


# ── Bulk VIN Job ──────────────────────────────────────────────────────────────

class BulkVinJobCreate(BaseModel):
    vins:            List[str] = Field(..., min_length=1, max_length=500)
    source_type:     Optional[str] = None
    source_file_url: Optional[str] = None


class BulkVinJob(BaseModel):
    job_id:          str  = Field(default_factory=lambda: str(uuid.uuid4()))
    dealer_id:       str
    status:          JobStatus            = JobStatus.pending
    total_vins:      int                  = 0
    processed_vins:  int                  = 0
    source_type:     Optional[str]        = None
    source_file_url: Optional[str]        = None
    error_message:   Optional[str]        = None
    created_at:      datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    updated_at:      datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
