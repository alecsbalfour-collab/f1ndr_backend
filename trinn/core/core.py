# f1ndr-backend/trinn/core/core.py
"""
DICT-aligned TRINN core orchestration with enterprise features.
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from trinn.config.config import get_trinn_config
from trinn.db.trinn_repo import get_task_repo
from trinn.utils.scheduler import get_scheduler
from trinn.core.exceptions_core import TrinnError, ValidationError
from scrapers.module import SCRAPER_CLASSES, run_scraper
from f1ndr.vin.decode import decode_vin
from listr.core.core import update_listing


logger = logging.getLogger(__name__)


async def run_task(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute TRINN task with enterprise error handling and retry logic.
    
    Args:
        data: Task data containing task type and parameters
        
    Returns:
        Dictionary with task results and metadata
    """
    config = get_trinn_config()
    task_type = data.get("task")
    
    logger.info(f"Executing TRINN task: {task_type}")
    
    try:
        if task_type == "scrape" and config["enable_scraper_tasks"]:
            return await _execute_scrape_task(data, config)
        elif task_type == "vin" and config["enable_vin_tasks"]:
            return await _execute_vin_task(data, config)
        elif task_type == "sync" and config["enable_listing_sync"]:
            return await _execute_sync_task(data, config)
        else:
            raise ValidationError(f"Invalid or disabled trinn task: {task_type}")
            
    except Exception as e:
        logger.error(f"Task execution failed: {e}")
        raise TrinnError(f"Task execution failed: {str(e)}")


async def _execute_scrape_task(data: Dict[str, Any], config) -> Dict[str, Any]:
    """Execute scraper task with enterprise error handling."""
    platform = data.get("platform")
    if platform not in SCRAPER_CLASSES:
        raise ValidationError(f"Unsupported scraper platform: {platform}")

    # Retries, backoff and circuit breaking are handled inside the scraper.
    result = await run_scraper(platform, data.get("query"))
    if not result["success"]:
        raise TrinnError(f"Scraper task failed for {platform}: {result['error']}")

    return {
        "task": "scrape",
        "platform": platform,
        "status": "completed",
        "result": result,
        "timestamp": datetime.utcnow().isoformat(),
    }


async def _execute_vin_task(data: Dict[str, Any], config) -> Dict[str, Any]:
    """Execute VIN decode task with enterprise error handling."""
    vin = data.get("vin")
    
    if not vin:
        raise ValidationError("VIN is required for VIN task")
    
    try:
        decoded = decode_vin(vin)
        
        return {
            "task": "vin",
            "vin": vin,
            "status": "completed",
            "result": decoded,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        raise TrinnError(f"VIN decode task failed: {str(e)}")


async def _execute_sync_task(data: Dict[str, Any], config) -> Dict[str, Any]:
    """Execute listing sync task with enterprise error handling."""
    platform = data.get("platform")
    listing = data.get("listing")
    
    if not platform or not listing:
        raise ValidationError("Platform and listing are required for sync task")
    
    try:
        result = update_listing(platform, listing)
        
        return {
            "task": "sync",
            "platform": platform,
            "status": "completed",
            "result": result,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        raise TrinnError(f"Sync task failed: {str(e)}")


async def schedule_task(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Schedule TRINN task with enterprise scheduling logic.
    
    Args:
        data: Task data containing scheduling parameters
        
    Returns:
        Dictionary with scheduling confirmation and metadata
    """
    config = get_trinn_config()
    interval = data.get("interval", config["default_interval_hours"])
    
    logger.info(f"Scheduling TRINN task with interval: {interval} hours")
    
    try:
        # Calculate next run time
        next_run = datetime.utcnow() + timedelta(hours=interval)
        
        # Schedule the task
        task_id = await get_scheduler().schedule_interval(data, interval)
        
        # Save task to database when a repository has been initialized
        try:
            await get_task_repo().insert({**data, "task_id": task_id})
        except RuntimeError:
            logger.warning("Task repository not initialized; task scheduled in memory only")
        
        return {
            "scheduled": True,
            "task_id": task_id,
            "interval_hours": interval,
            "next_run": next_run.isoformat(),
            "status": "scheduled",
            "timestamp": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Task scheduling failed: {e}")
        raise TrinnError(f"Task scheduling failed: {str(e)}")


async def schedule_sync(data: Dict[str, Any], interval_hours: int) -> Dict[str, Any]:
    """
    Schedule sync task with enterprise logic.
    
    Args:
        data: Sync task data
        interval_hours: Scheduling interval in hours
        
    Returns:
        Dictionary with scheduling confirmation
    """
    sync_data = {
        "task": "sync",
        "platform": data.get("platform"),
        "listing": data,
        "interval": interval_hours,
    }
    
    return await schedule_task(sync_data)
