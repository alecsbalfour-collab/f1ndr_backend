# f1ndr-backend/watchr/data/watchr_data.py
"""
State payload builder.
"""

def build_state_payload(trigger: dict) -> dict:
    return {
        "state": f"state_for_{trigger.get('trigger')}",
        "timestamp": trigger.get("timestamp"),
    }
