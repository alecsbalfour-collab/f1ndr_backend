"""watchr alert and subscription models."""

from typing import ClassVar, FrozenSet, Optional

from pydantic import Field

from api.schemas.common import OpenPayload, Record
from api.schemas.list_schemas import Category, Subcategory


class Alert(OpenPayload):
    # Owner is the authenticated caller; set by the route, never taken from the body.
    server_fields: ClassVar[FrozenSet[str]] = frozenset({"user_id"})
    name: str = Field(..., min_length=1, max_length=100)
    query: Optional[str] = Field(None, max_length=200)
    category: Optional[Category] = None
    subcategory: Optional[Subcategory] = None
    make: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    year_min: Optional[int] = Field(None, ge=1886, le=2100)
    year_max: Optional[int] = Field(None, ge=1886, le=2100)
    price_min: Optional[float] = Field(None, ge=0)
    price_max: Optional[float] = Field(None, ge=0)


class Subscription(OpenPayload):
    server_fields: ClassVar[FrozenSet[str]] = frozenset({"user_id"})
    name: str = Field(..., min_length=1, max_length=100)


class AlertOut(Record):
    alert_id: Optional[str] = None
    name: str
    user_id: Optional[str] = None
    status: Optional[str] = None
    query: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    year_min: Optional[int] = None
    year_max: Optional[int] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class SubscriptionOut(Record):
    subscription_id: Optional[str] = None
    name: str
    user_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
