"""
Config for marketplace posting.
"""

def get_listr_config() -> dict:
    return {
        "supported_platforms": [
            "kijiji",
            "facebook",
            "autotrader",
            "craigslist",
            "ebay"
        ],
        "max_title_length": 120,
        "sync_enabled": True,
        "sync_interval_hours": 24,
    }
