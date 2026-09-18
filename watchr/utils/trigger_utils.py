# f1ndr-backend/watchr/utils/trigger_utils.py
"""
Trigger utilities.
"""

def build_trigger_name(event_type: str) -> str:
    return f"trigger_{event_type.lower()}"
