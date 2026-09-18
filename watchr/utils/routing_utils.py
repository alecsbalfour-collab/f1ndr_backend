# f1ndr-backend/watchr/utils/routing_utils.py
"""
Routing utilities.
"""

def route_event(event_type: str) -> str:
    return f"route_for_{event_type}"
