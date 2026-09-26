"""
Config for listing creation.
"""

def get_sellr_config() -> dict:
    return {
        "feature_key": "sellr",
        "feature_version": "1.0.0",
        "enabled": True,

        "max_title_length": 120,
        "min_price": 0,

        "optimize_title": True,
        "optimize_description": True,

        "enable_vin_autofill": True,
        "enable_vin_validation": True,

        "allow_multi_platform": True,
        "default_platforms": ["kijiji", "facebook", "autotrader"],

        "auto_price": True,
        "price_floor_percent": 0.85,
        "price_ceiling_percent": 1.15,

        "enable_watchr_alerts": True,

        "auto_sync_interval_hours": 24,
    }


get_listings_config = get_sellr_config
