"""
Config for f1ndr intelligence engine.
"""

def get_f1ndr_config() -> dict:
    return {
        # Search behaviour
        "max_results": 100,
        "default_sort": "price",

        # Intelligence toggles
        "enable_vin": True,
        "enable_market_value": True,
        "enable_duplicates": True,
        "enable_fraud": True,

        # Duplicate detection
        "duplicate_title_threshold": 0.85,
        "duplicate_price_delta": 0.05,

        # Fraud detection
        "fraud_price_floor_factor": 0.6,
        "fraud_price_ceiling_factor": 1.6,
    }
