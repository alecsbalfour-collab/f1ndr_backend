"""watchr alert and subscription models."""

from typing import ClassVar, FrozenSet, Optional

from pydantic import Field

from api.schemas.common import OpenPayload


class Alert(OpenPayload):
    # Owner is the authenticated caller; set by the route, never taken from the body.
    server_fields: ClassVar[FrozenSet[str]] = frozenset({"user_id"})
    name: str = Field(..., min_length=1, max_length=100)
    user_id: Optional[str] = Field(None, max_length=100)
    query: Optional[str] = Field(None, max_length=200)
    make: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    year_min: Optional[int] = Field(None, ge=1886, le=2100)
    year_max: Optional[int] = Field(None, ge=1886, le=2100)
    price_min: Optional[float] = Field(None, ge=0)
    price_max: Optional[float] = Field(None, ge=0)


class Subscription(OpenPayload):
    server_fields: ClassVar[FrozenSet[str]] = frozenset({"user_id"})
    name: str = Field(..., min_length=1, max_length=100)
    user_id: Optional[str] = Field(None, max_length=100)
