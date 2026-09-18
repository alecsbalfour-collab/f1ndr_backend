# f1ndr-backend/processors/config/categories_config.py
"""
DICT-aligned categories configuration with enterprise features.
"""

import logging
from dataclasses import dataclass
from typing import Dict, Any, List


logger = logging.getLogger(__name__)


@dataclass
class CategoriesConfig:
    """Enterprise categories configuration with DICT patterns."""
    feature_key: str = "processors_categories"
    feature_version: str = "1.0.0"
    enabled: bool = True
    collection_name: str = "categories"
    supported_categories: List[str] = None
    
    def __post_init__(self):
        if self.supported_categories is None:
            self.supported_categories = ["vehicles", "real_estate", "electronics", "furniture"]
    
    def collection_name(self) -> str:
        """Get MongoDB collection name."""
        return self.collection_name
    
    def defaults(self) -> Dict[str, Any]:
        """Get default configuration with enterprise settings."""
        return {
            "enabled": self.enabled,
            "collection_name": self.collection_name,
            "supported_categories": self.supported_categories,
            "feature_key": self.feature_key,
            "feature_version": self.feature_version,
        }


categories_config = CategoriesConfig()
