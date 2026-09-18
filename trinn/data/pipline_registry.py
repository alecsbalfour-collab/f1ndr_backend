# f1ndr-backend/trinn/data/pipeline_registry.py
"""
DICT-aligned TRINN pipeline registry with enterprise features.
"""

import logging
from typing import Dict, Any, List, Callable


logger = logging.getLogger(__name__)


# Pipeline stage definitions
PIPELINE_STAGES = ["enrich", "normalize", "transform"]

# Pipeline stage configurations
PIPELINE_CONFIG = {
    "enrich": {
        "timeout": 60,
        "retry_count": 3,
        "enabled": True,
    },
    "normalize": {
        "timeout": 30,
        "retry_count": 2,
        "enabled": True,
    },
    "transform": {
        "timeout": 45,
        "retry_count": 2,
        "enabled": True,
    },
}


def get_pipeline_stages() -> List[str]:
    """
    Get available pipeline stages.
    
    Returns:
        List of pipeline stage names
    """
    return PIPELINE_STAGES.copy()


def get_stage_config(stage: str) -> Dict[str, Any]:
    """
    Get configuration for a specific pipeline stage.
    
    Args:
        stage: Stage name
        
    Returns:
        Stage configuration dictionary
    """
    if stage not in PIPELINE_CONFIG:
        logger.warning(f"Unknown pipeline stage: {stage}")
        return {}
    
    return PIPELINE_CONFIG[stage].copy()


def register_pipeline_stage(stage: str, config: Dict[str, Any]) -> None:
    """
    Register a new pipeline stage with enterprise validation.
    
    Args:
        stage: Stage name
        config: Stage configuration
    """
    if stage in PIPELINE_STAGES:
        logger.warning(f"Pipeline stage {stage} already exists, updating config")
    else:
        PIPELINE_STAGES.append(stage)
        logger.info(f"Registered new pipeline stage: {stage}")
    
    PIPELINE_CONFIG[stage] = config


def validate_pipeline_stages(stages: List[str]) -> bool:
    """
    Validate that all requested stages are registered.
    
    Args:
        stages: List of stage names to validate
        
    Returns:
        True if all stages are valid
    """
    invalid_stages = [stage for stage in stages if stage not in PIPELINE_STAGES]
    
    if invalid_stages:
        logger.warning(f"Invalid pipeline stages: {invalid_stages}")
        return False
    
    logger.debug("All pipeline stages are valid")
    return True
