# f1ndr_backend/api/middleware/abuse_middleware.py

from starlette.middleware.base import BaseHTTPMiddleware
from api.security.abuse_protection import abuse_guard


class AbuseMiddleware(BaseHTTPMiddleware):
    """
    Middleware that applies abuse protection to every incoming request.
    """

    async def dispatch(self, request, call_next):
        # Run abuse detection
        abuse_guard(request)

        # Continue processing
        response = await call_next(request)
        return response
