# f1ndr-backend/watchr/data/subscription_data.py
"""
Subscription payload builder.
"""

def build_subscription_payload(event: dict) -> dict:
    return {
        "event_type": event.get("event_type"),
        "subscriber": event.get("payload", {}).get("subscriber"),
        "timestamp": event.get("timestamp"),
    }
