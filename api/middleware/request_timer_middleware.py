import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from logging import getLogger

from api.observability.metrics import dec_active, inc_active, record_request

logger = getLogger("api.timer")


class RequestTimerMiddleware(BaseHTTPMiddleware):
    """
    Measures request execution time, logs it, and feeds the metrics counters.
    """

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        inc_active()
        try:
            response = await call_next(request)
        except Exception:
            dec_active()
            record_request(request.method, request.url.path, 500, (time.perf_counter() - start) * 1000)
            raise
        dec_active()

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        route = request.scope.get("route")
        path = getattr(route, "path", request.url.path) if route else request.url.path
        record_request(request.method, path, response.status_code, duration_ms)
        logger.info(
            "%s %s -> %s in %sms",
            request.method,
            path,
            response.status_code,
            duration_ms,
            extra={"method": request.method, "path": path,
                   "status_code": response.status_code, "duration_ms": duration_ms},
        )

        response.headers["X-Process-Time-ms"] = str(duration_ms)

        return response
