"""
Config for listing creation.
"""

def get_listings_config() -> dict:
    return {
        "max_title_length": 120,
        "min_price": 0,

        # Listing optimization
        "optimize_title": True,
        "optimize_description": True,

        # VIN intelligence
        "enable_vin_autofill": True,
        "enable_vin_validation": True,

        # Marketplace sync
        "allow_multi_platform": True,
        "default_platforms": ["kijiji", "facebook", "autotrader"],

        # Pricing intelligence
        "auto_price": True,
        "price_floor_percent": 0.85,
        "price_ceiling_percent": 1.15,

        # Watchr integration
        "enable_watchr_alerts": True,

        # Trinn automation
        "auto_sync_interval_hours": 24,
    }
