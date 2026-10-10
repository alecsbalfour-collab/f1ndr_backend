"""
Config for listing creation.
"""

import os

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
        "default_platforms": ["kijiji", "autotrader"],

        "auto_price": True,
        "price_floor_percent": 0.85,
        "price_ceiling_percent": 1.15,

        "enable_watchr_alerts": True,

        "auto_sync_interval_hours": 24,

        # Send-to-phone photo sessions
        "photo_session_ttl_minutes": int(os.getenv("PHOTO_SESSION_TTL_MINUTES", "30")),
        "photo_session_max_photos": int(os.getenv("PHOTO_SESSION_MAX_PHOTOS", "12")),
        "photo_max_bytes": int(os.getenv("PHOTO_MAX_BYTES", str(8 * 1024 * 1024))),
        # Public base used to build the phone link (defaults to the API origin path).
        "phone_upload_base_url": os.getenv("PHONE_UPLOAD_BASE_URL", ""),
    }


get_listings_config = get_sellr_config
