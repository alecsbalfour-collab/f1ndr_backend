# f1ndr-backend/watchr/config/routing_config.py
"""
Routing configuration for Watchr.
"""

def get_routing_config() -> dict:
    return {
        "default_route": "watchr",
        "allow_custom_routes": True,
    }
