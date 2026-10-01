"""
Shared API models: the response envelope every route returns, the error envelope the
exception handlers produce, and the base for open-ended payloads such as vehicle listings.
"""

from datetime import datetime, timezone
from typing import Any, ClassVar, Dict, FrozenSet, Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator
from typing_extensions import Annotated

T = TypeVar("T")

# Assigned by the server; clients can send them but they are dropped before validation.
SERVER_MANAGED_FIELDS = frozenset({"_id", "id", "created_at", "updated_at"})

# The pattern is checked before strip/upper-casing, hence the whitespace and (?i).
VIN = Annotated[str, StringConstraints(strip_whitespace=True, to_upper=True, pattern=r"(?i)^\s*[A-HJ-NPR-Z0-9]{17}\s*$")]
# Listings may carry pre-1981 VINs, which are shorter than 17 characters.
LooseVIN = Annotated[str, StringConstraints(strip_whitespace=True, to_upper=True, min_length=1, max_length=17)]


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class Pagination(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool

    @classmethod
    def build(cls, total: int, page: int, page_size: int) -> "Pagination":
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        return cls(total=total, page=page, page_size=page_size, total_pages=total_pages,
                   has_next=page < total_pages, has_previous=page > 1)


class Envelope(BaseModel, Generic[T]):
    success: bool = True
    message: str
    data: Optional[T] = None
    timestamp: str = Field(default_factory=_utcnow, json_schema_extra={"format": "date-time"})


class Page(Envelope[List[T]], Generic[T]):
    pagination: Pagination


class ErrorEnvelope(BaseModel):
    success: bool = False
    message: str
    timestamp: str = Field(json_schema_extra={"format": "date-time"})
    error_code: Optional[str] = None
    details: Optional[Any] = None
    request_id: Optional[str] = None


_ERROR_DESCRIPTIONS = {
    400: "Bad request",
    401: "Missing or invalid access token",
    403: "Forbidden",
    404: "Not found",
    409: "Conflict",
    422: "Request validation failed",
    423: "Account locked",
    429: "Rate limited",
    500: "Internal server error",
}


def error_responses(*status_codes: int) -> Dict[int, Dict[str, Any]]:
    """OpenAPI `responses` entries documenting the error envelope for the given status codes."""
    return {code: {"model": ErrorEnvelope, "description": _ERROR_DESCRIPTIONS[code]} for code in status_codes}


def ok(data: Any = None, message: str = "Operation successful") -> Dict[str, Any]:
    """Success body; the route's `response_model` validates it and fills `success`/`timestamp`."""
    return {"message": message, "data": data}


def paged(items: List[Any], total: int, page: int, page_size: int, message: str) -> Dict[str, Any]:
    return {"message": message, "data": items, "pagination": Pagination.build(total, page, page_size)}


class Record(BaseModel):
    """Stored document: declared fields are typed, anything else is returned as stored."""
    model_config = ConfigDict(extra="allow")


class OpenPayload(BaseModel):
    """
    Request body for open-ended documents. Declared fields are validated, undeclared keys pass
    through unchanged, server-managed keys are dropped, and Mongo operator/path keys are rejected.
    """
    model_config = ConfigDict(extra="allow", str_strip_whitespace=True)
    # Extra keys the server sets for this document type (e.g. the owner, taken from the token).
    server_fields: ClassVar[FrozenSet[str]] = frozenset()

    @model_validator(mode="before")
    @classmethod
    def _clean_keys(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        bad = [k for k in data if not isinstance(k, str) or not k or k.startswith("$") or "." in k]
        if bad:
            raise ValueError("Field names must be non-empty and must not start with '$' or contain '.'")
        dropped = SERVER_MANAGED_FIELDS | cls.server_fields
        return {k: v for k, v in data.items() if k not in dropped}

    def to_data(self) -> Dict[str, Any]:
        """Only the keys the client actually sent, so partial updates don't overwrite with nulls."""
        return self.model_dump(exclude_unset=True)


class VersionInfo(BaseModel):
    version: str
    description: str
    status: str
    api_type: str
    flutterflow_compatible: bool
    enterprise_features: bool
    timestamp: str


class ModuleStatus(Record):
    module: str
    status: str
    feature_key: Optional[str] = None
    feature_version: Optional[str] = None
    enabled: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None
