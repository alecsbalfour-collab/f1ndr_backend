import re
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from api.observability.logging import (
    parse_traceparent,
    request_id_var,
    span_id_var,
    trace_id_var,
)

REQUEST_ID_HEADER = "X-Request-ID"
TRACEPARENT_HEADER = "traceparent"
_VALID_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{8,128}$")


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Assigns a unique request ID to every incoming request.
    A well-formed inbound X-Request-ID (e.g. from a proxy) is kept for tracing.
    Also propagates W3C traceparent ids into the log context.
    """

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get(REQUEST_ID_HEADER, "")
        if not _VALID_REQUEST_ID.match(request_id):
            request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        trace_id, span_id = parse_traceparent(request.headers.get(TRACEPARENT_HEADER))
        request.state.trace_id = trace_id
        request.state.span_id = span_id

        tokens = (
            request_id_var.set(request_id),
            trace_id_var.set(trace_id),
            span_id_var.set(span_id),
        )
        try:
            response = await call_next(request)
        finally:
            request_id_var.reset(tokens[0])
            trace_id_var.reset(tokens[1])
            span_id_var.reset(tokens[2])
        response.headers[REQUEST_ID_HEADER] = request_id

        return response
