"""
Global exception handlers. Every error leaves the API in the `utils.response_builder`
envelope with a request ID; unexpected exceptions never expose internals to the client.
"""

import logging
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

from api.errors.api_exceptions import APIException
from dealr.core.errors_core import DealrError
from trinn.core.exceptions_core import TrinnError, ValidationError as TrinnValidationError, ExternalServiceError
from utils.response_builder import error_response

logger = logging.getLogger("api.error")


def _request_id(request: Request):
    return getattr(request.state, "request_id", None)


def _status_code_name(status_code: int) -> str:
    try:
        return HTTPStatus(status_code).name
    except ValueError:
        return "ERROR"


async def api_exception_handler(request: Request, exc: APIException):
    return error_response(
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details or None,
        error_code=_status_code_name(exc.status_code),
        request_id=_request_id(request),
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    detail = exc.detail
    response = error_response(
        message=detail if isinstance(detail, str) else HTTPStatus(exc.status_code).phrase,
        status_code=exc.status_code,
        details=None if isinstance(detail, str) else jsonable_encoder(detail),
        error_code=_status_code_name(exc.status_code),
        request_id=_request_id(request),
    )
    if exc.headers:
        response.headers.update(exc.headers)
    return response


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Drop the echoed input so submitted values (e.g. passwords) never come back in errors.
    errors = [{k: v for k, v in err.items() if k != "input"} for err in exc.errors()]
    return error_response(
        message="Validation failed",
        status_code=422,
        details={"validation_errors": jsonable_encoder(errors)},
        error_code="VALIDATION_ERROR",
        request_id=_request_id(request),
    )


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    # Sync on purpose: SlowAPIMiddleware only calls synchronous handlers.
    logger.warning("Rate limit exceeded: %s %s (%s)", request.method, request.url.path, exc.detail)
    response = error_response(
        message="Too many requests",
        status_code=429,
        error_code="RATE_LIMITED",
        request_id=_request_id(request),
    )
    response.headers["Retry-After"] = str(exc.limit.limit.get_expiry())
    return response


async def dealr_exception_handler(request: Request, exc: DealrError):
    return error_response(
        message=exc.message,
        status_code=exc.status_code,
        details=exc.detail,
        error_code=exc.error_code,
        request_id=_request_id(request),
    )


async def unhandled_exception_handler(request: Request, exc: Exception):
    request_id = _request_id(request)
    logger.error(
        "Unhandled exception on %s %s (request_id=%s)",
        request.method,
        request.url.path,
        request_id,
        exc_info=exc,
    )
    return error_response(
        message="Internal server error",
        status_code=500,
        error_code="INTERNAL_ERROR",
        request_id=request_id,
    )


async def trinn_exception_handler(request: Request, exc: TrinnError):
    # exc.message embeds the underlying error (upstream details, internals) — keep it in
    # the logs and return a generic message with the typed error_code instead.
    if isinstance(exc, TrinnValidationError):
        status_code, message = 400, "Invalid task parameters"
    elif isinstance(exc, ExternalServiceError):
        status_code, message = 502, "Upstream service failed during task execution"
    else:
        status_code, message = 502, "Task execution failed"
    return error_response(
        message=message,
        status_code=status_code,
        error_code=exc.error_code,
        request_id=_request_id(request),
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(APIException, api_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    app.add_exception_handler(DealrError, dealr_exception_handler)
    app.add_exception_handler(TrinnError, trinn_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
