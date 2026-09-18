# f1ndr-backend/f1ndr/config/config.py
"""
DICT-aligned f1ndr configuration with enterprise features.
"""

import logging
from dataclasses import dataclass
from typing import List, Dict, Any


logger = logging.getLogger(__name__)


@dataclass
class F1ndrConfig:
    """Enterprise f1ndr configuration with DICT patterns."""
    feature_key: str = "f1ndr"
    feature_version: str = "1.0.0"
    enabled: bool = True
    
    # API configuration
    api_version: str = "1.0.0"
    enabled_features: List[str] = None
    
    # Search behaviour
    max_results: int = 100
    default_sort: str = "price"
    
    # Intelligence toggles
    enable_vin: bool = True
    enable_market_value: bool = True
    enable_duplicates: bool = True
    enable_fraud: bool = True
    
    # Duplicate detection
    duplicate_title_threshold: float = 0.85
    duplicate_price_delta: float = 0.05
    
    # Fraud detection
    fraud_price_floor_factor: float = 0.6
    fraud_price_ceiling_factor: float = 1.6
    
    def __post_init__(self):
        if self.enabled_features is None:
            self.enabled_features = ["vin_decode", "market_value", "duplicate_detection", "fraud_detection"]


def get_f1ndr_config() -> Dict[str, Any]:
    """Get f1ndr configuration with enterprise settings."""
    config = F1ndrConfig()
    
    return {
        "feature_key": config.feature_key,
        "feature_version": config.feature_version,
        "enabled": config.enabled,
        "api_version": config.api_version,
        "enabled_features": config.enabled_features,
        "max_results": config.max_results,
        "default_sort": config.default_sort,
        "enable_vin": config.enable_vin,
        "enable_market_value": config.enable_market_value,
        "enable_duplicates": config.enable_duplicates,
        "enable_fraud": config.enable_fraud,
        "duplicate_title_threshold": config.duplicate_title_threshold,
        "duplicate_price_delta": config.duplicate_price_delta,
        "fraud_price_floor_factor": config.fraud_price_floor_factor,
        "fraud_price_ceiling_factor": config.fraud_price_ceiling_factor,
    }
