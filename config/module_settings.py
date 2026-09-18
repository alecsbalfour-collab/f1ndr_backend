# f1ndr-backend/watchr/config/module_settings.py
"""
General Watchr module settings.
"""

def get_module_settings() -> dict:
    return {
        "strict_mode": False,
        "logging_enabled": True,
    }
