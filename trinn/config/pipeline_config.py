# f1ndr-backend/trinn/config/pipeline_config.py
"""
DICT-aligned TRINN pipeline configuration with enterprise features.
"""

import logging
from dataclasses import dataclass
from typing import List, Dict, Any


logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """Enterprise pipeline configuration with DICT patterns."""
    feature_key: str = "trinn_pipeline"
    feature_version: str = "1.0.0"
    enabled: bool = True
    
    # Pipeline stages
    stages: List[str] = None
    async_processing: bool = True
    parallel_stages: bool = False
    
    # Stage configuration
    stage_timeout: int = 300
    max_concurrent_stages: int = 5
    
    # Error handling
    continue_on_error: bool = False
    rollback_on_failure: bool = True
    
    # Validation
    validate_inputs: bool = True
    validate_outputs: bool = True
    
    def __post_init__(self):
        if self.stages is None:
            self.stages = ["enrich", "normalize", "transform"]


def get_pipeline_config() -> PipelineConfig:
    """Get pipeline configuration."""
    config = PipelineConfig()
    logger.info(f"Pipeline config loaded: {config.feature_key} with stages: {config.stages}")
    return config


def get_pipeline_state() -> Dict[str, Any]:
    """Get current pipeline state for monitoring."""
    return {
        "active_pipelines": 0,
        "completed_pipelines": 0,
        "failed_pipelines": 0,
        "average_duration_ms": 0,
    }
