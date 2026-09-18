# f1ndr-backend/watchr/config/events_config.py
"""
Event configuration for Watchr.
"""

def get_events_config() -> dict:
    return {
        "enabled": True,
        "max_events": 500,
        "allow_dynamic_events": True,
    }
