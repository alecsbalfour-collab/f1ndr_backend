# scrapers/db/cache_db.py

import time

_cache_store: dict[str, tuple[dict, float | None]] = {}


async def cache_set(key: str, value: dict, ttl: float | None = None) -> None:
    """
    Store a value in the in-memory scraper cache.
    Entries with a ttl (seconds) expire automatically.
    """
    expires_at = time.monotonic() + ttl if ttl else None
    _cache_store[key] = (value, expires_at)


async def cache_get(key: str) -> dict | None:
    """
    Retrieve a cached value.
    """
    entry = _cache_store.get(key)
    if entry is None:
        return None
    value, expires_at = entry
    if expires_at is not None and time.monotonic() >= expires_at:
        _cache_store.pop(key, None)
        return None
    return value


async def cache_delete(key: str) -> None:
    """
    Remove a cached value.
    """
    _cache_store.pop(key, None)


async def cache_clear() -> None:
    """
    Clear all cached entries.
    """
    _cache_store.clear()
