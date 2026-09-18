# f1ndr-backend/watchr/core/validation_core.py
"""
Watchr validation utilities.
"""

def require_fields(data: dict, fields: list) -> bool:
    missing = [f for f in fields if f not in data]
    return len(missing) == 0
