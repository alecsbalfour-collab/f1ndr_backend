# f1ndr-backend/watchr/utils/format_utils.py
"""
Formatting utilities.
"""

def format_event(event: dict) -> str:
    return f"[{event.get('timestamp')}] {event.get('event_type')}"
