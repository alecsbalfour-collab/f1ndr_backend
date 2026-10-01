from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from api.security.secure_header import apply_secure_headers


class SecureHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds the security headers from `apply_secure_headers` to every response.
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        apply_secure_headers(response)
        return response
