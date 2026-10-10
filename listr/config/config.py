"""
Config for marketplace posting.
"""

def get_listr_config() -> dict:
    return {
        "feature_key": "listr",
        "feature_version": "1.0.0",
        "enabled": True,
        "supported_platforms": [
            "kijiji",
            "autotrader",
            "craigslist",
            "ebay"
        ],
        "max_title_length": 120,
        "sync_enabled": True,
        "sync_interval_hours": 24,
    }
