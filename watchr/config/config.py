"""
Config for watchr alerts and subscriptions.
"""


def get_watchr_config() -> dict:
    return {
        "feature_key": "watchr",
        "feature_version": "1.0.0",
        "enabled": True,

        "alert_scan_limit": 100,
    }
