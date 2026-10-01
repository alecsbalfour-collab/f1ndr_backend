import re
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

REQUEST_ID_HEADER = "X-Request-ID"
_VALID_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{8,128}$")


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Assigns a unique request ID to every incoming request.
    A well-formed inbound X-Request-ID (e.g. from a proxy) is kept for tracing.
    """

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get(REQUEST_ID_HEADER, "")
        if not _VALID_REQUEST_ID.match(request_id):
            request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id

        return response
