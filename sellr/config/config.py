"""
Config for listing creation.
"""

def get_listings_config() -> dict:
    return {
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
