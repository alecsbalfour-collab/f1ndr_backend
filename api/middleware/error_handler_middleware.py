from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from api.errors.exception_handlers import unhandled_exception_handler


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Global error handler middleware.
    Converts unhandled exceptions into the unified JSON error response inside the
    middleware stack, so the response still carries the request ID and security headers.
    HTTP/API exceptions are handled earlier by the handlers in `api.errors.exception_handlers`.
    """

    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as exc:
            return await unhandled_exception_handler(request, exc)
