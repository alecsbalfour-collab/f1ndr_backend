# f1ndr-backend/watchr/utils/event_utils.py
"""
Event utilities.
"""

def normalize_event_type(event_type: str) -> str:
    return event_type.lower().strip()
