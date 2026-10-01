# f1ndr_backend/api/security/abuse_protection.py

import time
from fastapi import Request
from api.errors import raise_api_error

# In‑memory abuse tracking (per‑IP request timestamps)
ABUSE_CACHE: dict[str, list[float]] = {}

# Thresholds
WINDOW_SECONDS = 60          # sliding window
MAX_REQUESTS_PER_WINDOW = 40 # 40 requests per minute per IP


def abuse_guard(request: Request):
    """
    Tracks request frequency per IP and blocks abusive clients.
    """
    ip = request.client.host
    now = time.time()

    # Get existing timestamps for this IP
    history = ABUSE_CACHE.get(ip, [])

    # Keep only timestamps within the sliding window
    history = [t for t in history if now - t < WINDOW_SECONDS]
    history.append(now)

    ABUSE_CACHE[ip] = history

    # If too many requests in the window → block
    if len(history) > MAX_REQUESTS_PER_WINDOW:
        raise_api_error(
            status_code=429,
            message="Too many requests",
            details={
                "ip": ip,
                "count": len(history),
                "window_seconds": WINDOW_SECONDS,
            },
        )
