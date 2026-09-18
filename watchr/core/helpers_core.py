# f1ndr-backend/watchr/core/helpers_core.py
"""
Watchr helper utilities.
"""

def safe_get(data: dict, key: str, default=None):
    return data.get(key, default)
