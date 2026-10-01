import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from logging import getLogger

logger = getLogger("api.timer")


class RequestTimerMiddleware(BaseHTTPMiddleware):
    """
    Measures request execution time and logs it.
    """

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()

        response = await call_next(request)

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.info(
            "%s %s -> %s in %sms (request_id=%s)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            getattr(request.state, "request_id", None),
        )

        response.headers["X-Process-Time-ms"] = str(duration_ms)

        return response
