# f1ndr-backend/trinn/config/transform_config.py
"""
DICT-aligned TRINN transform stage configuration with enterprise features.
"""

import logging
from dataclasses import dataclass
from typing import List, Dict, Any


logger = logging.getLogger(__name__)


@dataclass
class TransformConfig:
    """Enterprise transform stage configuration with DICT patterns."""
    feature_key: str = "trinn_transform"
    feature_version: str = "1.0.0"
    enabled: bool = True
    
    # Processing configuration
    max_batch_size: int = 100
    timeout: int = 60
    
    # Transformation rules
    canonical_source_mapping: Dict[str, str] = None
    field_transformations: Dict[str, str] = None
    
    # Output format
    output_format: str = "canonical"
    include_metadata: bool = True
    
    # Error handling
    continue_on_transform_error: bool = True
    strict_mapping: bool = False
    
    def __post_init__(self):
        if self.canonical_source_mapping is None:
            self.canonical_source_mapping = {}
        if self.field_transformations is None:
            self.field_transformations = {}


def get_transform_config() -> TransformConfig:
    """Get transform stage configuration."""
    config = TransformConfig()
    logger.info(f"Transform config loaded: {config.feature_key}")
    return config
