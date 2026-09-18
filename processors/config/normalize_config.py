# f1ndr-backend/processors/config/normalize_config.py
"""
DICT-aligned normalize configuration with enterprise features.
"""

import logging
from dataclasses import dataclass
from typing import Dict, Any


logger = logging.getLogger(__name__)


@dataclass
class NormalizeConfig:
    """Enterprise normalize configuration with DICT patterns."""
    feature_key: str = "processors_normalize"
    feature_version: str = "1.0.0"
    enabled: bool = True
    collection_name: str = "normalized"
    strict_mode: bool = True
    normalize_fields: list = None
    
    def __post_init__(self):
        if self.normalize_fields is None:
            self.normalize_fields = ["title", "description", "location"]
    
    def collection_name(self) -> str:
        """Get MongoDB collection name."""
        return self.collection_name
    
    def defaults(self) -> Dict[str, Any]:
        """Get default configuration with enterprise settings."""
        return {
            "enabled": self.enabled,
            "collection_name": self.collection_name,
            "strict_mode": self.strict_mode,
            "normalize_fields": self.normalize_fields,
            "feature_key": self.feature_key,
            "feature_version": self.feature_version,
        }


normalize_config = NormalizeConfig()
