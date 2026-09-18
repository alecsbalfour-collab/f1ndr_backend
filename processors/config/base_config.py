# f1ndr-backend/processors/config/base_config.py
"""
DICT-aligned base configuration with enterprise features.
"""

import logging
from dataclasses import dataclass
from typing import Dict, Any


logger = logging.getLogger(__name__)


@dataclass
class BaseConfig:
    """Enterprise base configuration with DICT patterns."""
    feature_key: str = "processors_base"
    feature_version: str = "1.0.0"
    enabled: bool = True
    max_retries: int = 3
    timeout: int = 30
    
    def defaults(self) -> Dict[str, Any]:
        """Get default configuration with enterprise settings."""
        return {
            "enabled": self.enabled,
            "max_retries": self.max_retries,
            "timeout": self.timeout,
            "feature_key": self.feature_key,
            "feature_version": self.feature_version,
        }


base_config = BaseConfig()
