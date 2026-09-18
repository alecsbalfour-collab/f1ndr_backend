# f1ndr-backend/trinn/config/normalize_config.py
"""
DICT-aligned TRINN normalize stage configuration with enterprise features.
"""

import logging
from dataclasses import dataclass
from typing import List, Dict, Any


logger = logging.getLogger(__name__)


@dataclass
class NormalizeConfig:
    """Enterprise normalize stage configuration with DICT patterns."""
    feature_key: str = "trinn_normalize"
    feature_version: str = "1.0.0"
    enabled: bool = True
    
    # Processing configuration
    strict: bool = True
    normalize_case: bool = True
    trim_whitespace: bool = True
    
    # Field normalization rules
    normalize_fields: List[str] = None
    field_mappings: Dict[str, str] = None
    
    # Validation
    validate_required_fields: bool = True
    required_fields: List[str] = None
    
    def __post_init__(self):
        if self.normalize_fields is None:
            self.normalize_fields = ["title", "description", "location"]
        if self.field_mappings is None:
            self.field_mappings = {}
        if self.required_fields is None:
            self.required_fields = ["id", "title", "price"]


def get_normalize_config() -> NormalizeConfig:
    """Get normalize stage configuration."""
    config = NormalizeConfig()
    logger.info(f"Normalize config loaded: {config.feature_key}")
    return config
