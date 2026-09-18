# f1ndr-backend/watchr/data/trigger_data.py
"""
Trigger payload builder.
"""

def build_trigger_payload(subscription: dict) -> dict:
    return {
        "trigger": f"trigger_for_{subscription.get('event_type')}",
        "timestamp": subscription.get("timestamp"),
    }
