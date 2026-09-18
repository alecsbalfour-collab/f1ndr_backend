"""
trinn module entrypoint.
"""

import os

def get_trinn_config() -> dict:
    """Get trinn module configuration."""
    return {
        "enable_scraper_tasks": os.getenv("ENABLE_SCRAPER_TASKS", "true").lower() == "true",
        "enable_vin_tasks": os.getenv("ENABLE_VIN_TASKS", "true").lower() == "true",
        "enable_watchr_tasks": os.getenv("ENABLE_WATCHR_TASKS", "true").lower() == "true",
        "enable_listing_sync": os.getenv("ENABLE_LISTING_SYNC", "true").lower() == "true",
        "default_interval_hours": int(os.getenv("DEFAULT_INTERVAL_HOURS", "1")),
    }

# Import moved to function level to avoid circular import
def run(action: str, data: dict):
    from trinn.core.core import run_task, schedule_task
    
    if action == "run":
        return run_task(data)
    if action == "schedule":
        return schedule_task(data)
    raise ValueError("Invalid trinn action")
