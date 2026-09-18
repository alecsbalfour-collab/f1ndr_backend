# f1ndr-backend/pipelines/config/pipline_config.py
"""
DICT-aligned pipeline configuration with enterprise features.
"""

import logging
from dataclasses import dataclass
from typing import Dict, Any, List


logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """Enterprise pipeline configuration with DICT patterns."""
    feature_key: str = "pipelines"
    feature_version: str = "1.0.0"
    enabled: bool = True
    max_batch: int = 100
    max_retries: int = 3
    timeout: int = 60
    stages: List[str] = None
    
    def __post_init__(self):
        if self.stages is None:
            self.stages = ["validate", "transform", "ingest"]
    
    def defaults(self) -> Dict[str, Any]:
        """Get default configuration with enterprise settings."""
        return {
            "enabled": self.enabled,
            "max_batch": self.max_batch,
            "max_retries": self.max_retries,
            "timeout": self.timeout,
            "stages": self.stages,
            "feature_key": self.feature_key,
            "feature_version": self.feature_version,
        }


pipeline_config = PipelineConfig()
