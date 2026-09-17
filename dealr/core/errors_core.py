"""dealr.core.errors_core — Structured exception hierarchy and FastAPI handlers."""

from typing import Any, Dict, Optional

from fastapi import Request
from fastapi.responses import JSONResponse


class DealrError(Exception):
    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"

    def __init__(self, message: str, detail: Optional[Any] = None) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"error": self.error_code, "message": self.message}
        if self.detail is not None:
            payload["detail"] = self.detail
        return payload


class NotFoundError(DealrError):
    status_code = 404
    error_code = "NOT_FOUND"


class AuthError(DealrError):
    status_code = 401
    error_code = "UNAUTHORIZED"


class ForbiddenError(DealrError):
    status_code = 403
    error_code = "FORBIDDEN"


class ValidationError(DealrError):
    status_code = 422
    error_code = "VALIDATION_ERROR"


class ConflictError(DealrError):
    status_code = 409
    error_code = "CONFLICT"


class VinDecodeError(DealrError):
    status_code = 422
    error_code = "VIN_DECODE_ERROR"


class ExternalServiceError(DealrError):
    status_code = 502
    error_code = "EXTERNAL_SERVICE_ERROR"


async def dealr_error_handler(request: Request, exc: DealrError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=exc.to_dict())


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"error": "INTERNAL_ERROR", "message": "An unexpected error occurred."},
    )
