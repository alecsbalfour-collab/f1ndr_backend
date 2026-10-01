import logging
from datetime import datetime, timezone
from typing import Iterable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# When the unversioned paths were deprecated in favour of /api/v1 (RFC 9745 structured date).
LEGACY_DEPRECATED_AT = int(datetime(2026, 9, 27, tzinfo=timezone.utc).timestamp())


class DeprecationMiddleware(BaseHTTPMiddleware):
    """
    Marks responses served from the deprecated unversioned API paths with `Deprecation`
    and a `Link` to the versioned successor, and logs each such path once per process.
    """

    def __init__(self, app, prefixes: Iterable[str], successor_prefix: str):
        super().__init__(app)
        self.prefixes = tuple(prefixes)
        self.successor_prefix = successor_prefix
        self._seen: set = set()

    def _is_legacy(self, path: str) -> bool:
        return any(path == p or path.startswith(p + "/") for p in self.prefixes)

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        path = request.url.path
        if self._is_legacy(path):
            response.headers["Deprecation"] = f"@{LEGACY_DEPRECATED_AT}"
            response.headers["Link"] = f'<{self.successor_prefix}{path}>; rel="successor-version"'
            # Keyed by route template (not the raw path) so IDs in URLs can't grow the set.
            route = getattr(request.scope.get("route"), "path", None)
            if route and (request.method, route) not in self._seen:
                self._seen.add((request.method, route))
                logger.info("Deprecated unversioned API path used: %s %s", request.method, route)
        return response
