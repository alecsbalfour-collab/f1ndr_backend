# f1ndr-backend/watchr/data/event_definitions.py
"""
Event payload builder.
"""

def build_event_payload(raw: dict) -> dict:
    return {
        "event_type": raw.get("event_type"),
        "payload": raw,
        "timestamp": raw.get("timestamp"),
    }
