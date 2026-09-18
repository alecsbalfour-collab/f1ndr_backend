# f1ndr-backend/trinn/config/enrich_config.py
"""
DICT-aligned TRINN enrich stage configuration with enterprise features.
"""

import logging
from dataclasses import dataclass
from typing import List, Dict, Any


logger = logging.getLogger(__name__)


@dataclass
class EnrichConfig:
    """Enterprise enrich stage configuration with DICT patterns."""
    feature_key: str = "trinn_enrich"
    feature_version: str = "1.0.0"
    enabled: bool = True
    
    # Processing configuration
    max_batch_size: int = 100
    timeout: int = 60
    
    # Data enrichment rules
    enrich_sources: List[str] = None
    enrich_metadata: bool = True
    enrich_source_validation: bool = True
    
    # Error handling
    continue_on_missing_source: bool = True
    strict_validation: bool = False
    
    def __post_init__(self):
        if self.enrich_sources is None:
            self.enrich_sources = ["metadata", "source", "timestamp"]


def get_enrich_config() -> EnrichConfig:
    """Get enrich stage configuration."""
    config = EnrichConfig()
    logger.info(f"Enrich config loaded: {config.feature_key}")
    return config
