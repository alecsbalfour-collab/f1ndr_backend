# f1ndr-backend/watchr/utils/subscription_utils.py
"""
Subscription utilities.
"""

def normalize_subscriber(subscriber: str) -> str:
    return subscriber.lower().strip()
