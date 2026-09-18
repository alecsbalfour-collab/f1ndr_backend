"""
DICT-aligned TRINN configuration with enterprise features.
"""

import os
import logging
from dataclasses import dataclass
from typing import Dict, List, Any, Optional


logger = logging.getLogger(__name__)


@dataclass
class TrinnConfig:
    """Enterprise TRINN configuration with DICT patterns."""
    feature_key: str = "trinn"
    feature_version: str = "1.0.0"
    enabled: bool = True
    
    # Task processing flags
    enable_scraper_tasks: bool = True
    enable_vin_tasks: bool = True
    enable_watchr_tasks: bool = True
    enable_listing_sync: bool = True
    
    # Pipeline configuration
    default_interval_hours: int = 1
    max_retries: int = 3
    retry_delay: float = 1.0
    batch_size: int = 100
    
    # Database configuration
    db_collection_tasks: str = "trinn_tasks"
    db_collection_pipeline: str = "trinn_pipeline"
    
    # Logging configuration
    log_category: str = "trinn"
    log_level: str = "INFO"
    
    # Supported platforms
    supported_platforms: List[str] = None
    
    def __post_init__(self):
        if self.supported_platforms is None:
            self.supported_platforms = ["kijiji", "facebook", "autotrader", "craigslist", "ebay"]


def get_trinn_config() -> TrinnConfig:
    """Get TRINN module configuration from environment variables."""
    return TrinnConfig(
        enable_scraper_tasks=os.getenv("ENABLE_SCRAPER_TASKS", "true").lower() == "true",
        enable_vin_tasks=os.getenv("ENABLE_VIN_TASKS", "true").lower() == "true",
        enable_watchr_tasks=os.getenv("ENABLE_WATCHR_TASKS", "true").lower() == "true",
        enable_listing_sync=os.getenv("ENABLE_LISTING_SYNC", "true").lower() == "true",
        default_interval_hours=int(os.getenv("DEFAULT_INTERVAL_HOURS", "1")),
        max_retries=int(os.getenv("TRINN_MAX_RETRIES", "3")),
        retry_delay=float(os.getenv("TRINN_RETRY_DELAY", "1.0")),
        batch_size=int(os.getenv("TRINN_BATCH_SIZE", "100")),
        log_level=os.getenv("TRINN_LOG_LEVEL", "INFO"),
    )


# Import moved to function level to avoid circular import
def run(action: str, data: dict) -> dict:
    from trinn.core.core import run_task, schedule_task
    
    config = get_trinn_config()
    logger.info(f"TRINN action: {action} with config: {config.feature_key}")
    
    if action == "run":
        return run_task(data)
    if action == "schedule":
        return schedule_task(data)
    raise ValueError(f"Invalid trinn action: {action}")
