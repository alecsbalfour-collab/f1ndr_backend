DEALR_CONFIG = {
    "feature_key": "dealr",
    "feature_version": "1.0.0",
    "enabled": True,
    "db": {
        "collection_name": "dealr_accounts",
        "unique_fields": ["email", "external_id"],
        "indexes": [
            {"keys": [("email", 1)], "unique": True},
            {"keys": [("external_id", 1)], "unique": True},
            {"keys": [("name", 1)], "unique": False},
        ],
    },
    "defaults": {
        "status": "active",
        "timezone": "America/Edmonton",
        "max_active_listings": 5000,
    },
    "validation": {
        "allowed_statuses": ["active", "inactive", "suspended"],
        "min_name_length": 3,
        "max_name_length": 120,
    },
    "logging": {
        "log_category": "dealr",
        "log_level": "INFO",
    },
    "enable_vin_decode": True,
    "enable_market_value": True,
    "default_platforms": ["kijiji", "autotrader"],
    "sync_interval_hours": 24,
}

dealr_config = DEALR_CONFIG


def get_dealr_config() -> dict:
    return dict(DEALR_CONFIG)
