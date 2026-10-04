# f1ndr_backend/api/security/rate_limiter.py

from slowapi import Limiter
from slowapi.util import get_remote_address

# Global rate limiter instance
limiter = Limiter(
    key_func=get_remote_address,     # identifies clients by IP
    default_limits=["100/minute"],   # global default limit
    # Count per view function, not per URL: /api/v1 and the legacy aliases share one quota,
    # and path IDs (/listings/<id>) can't be used to get a fresh bucket per request.
    key_style="endpoint",
)

# Strict per-route limits for brute-force targets
LOGIN_RATE_LIMIT = "5/minute;20/hour"
REGISTER_RATE_LIMIT = "3/minute;10/hour"
PASSWORD_RESET_RATE_LIMIT = "3/minute;10/hour"
