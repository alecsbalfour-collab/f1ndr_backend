# f1ndr-backend/trinn/core/core.py
"""
DICT-aligned TRINN core orchestration with enterprise features.
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from trinn.config.config import get_trinn_config
from trinn.db.trinn_repo import tasks_store
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
        _require_task_enabled(task_type, config)
        if task_type == "scrape":
            return await _execute_scrape_task(data, config)
        elif task_type == "vin":
            return await _execute_vin_task(data, config)
        else:
            return await _execute_sync_task(data, config)

    except TrinnError:
        raise
    except Exception as e:
        logger.error(f"Task execution failed: {e}")
        raise TrinnError(f"Task execution failed: {str(e)}")


_TASK_FLAGS = {
    "scrape": "enable_scraper_tasks",
    "vin": "enable_vin_tasks",
    "sync": "enable_listing_sync",
}


def _require_task_enabled(task_type: Optional[str], config: Dict[str, Any]) -> None:
    """Reject unknown task types and tasks disabled via config flags."""
    flag = _TASK_FLAGS.get(task_type)
    if flag is None or not config[flag]:
        raise ValidationError(f"Invalid or disabled trinn task: {task_type}")


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
        result = await update_listing(platform, listing)
        
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
    _require_task_enabled(data.get("task"), config)
    interval = data.get("interval", config["default_interval_hours"])

    logger.info(f"Scheduling TRINN task with interval: {interval} hours")

    try:
        # Calculate next run time
        next_run = datetime.utcnow() + timedelta(hours=interval)

        # Schedule the task
        task_id = await get_scheduler().schedule_interval(data, interval, next_run=next_run)

        # Persist so the schedule survives a restart (best-effort: Mongo or in-memory)
        try:
            await tasks_store.upsert({
                "task_id": task_id,
                "task": data.get("task"),
                "task_data": data,
                "interval_hours": interval,
                "next_run": next_run.isoformat(),
                "enabled": True,
                "status": "scheduled",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            })
        except Exception as e:
            logger.warning(f"Task {task_id} scheduled in memory only; persistence failed: {e}")
        
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


def _merge_live(doc: Dict[str, Any], live: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Overlay live scheduler fields (next_run, run_count, last_run, enabled) onto a persisted doc."""
    return {**doc, **live} if live else doc


async def list_scheduled_tasks() -> list:
    """
    All known scheduled tasks: persisted documents overlaid with live scheduler state,
    plus any tasks only held in memory (persistence unavailable when they were scheduled).
    """
    scheduler = get_scheduler()
    live_by_id = {t["task_id"]: t for t in await scheduler.list_tasks()}
    tasks = []
    seen = set()
    for doc in await tasks_store.find(sort=("created_at", -1)):
        seen.add(doc["task_id"])
        tasks.append(_merge_live(doc, live_by_id.pop(doc["task_id"], None)))
    tasks.extend(live_by_id.values())
    return tasks


async def get_scheduled_task(task_id: str) -> Optional[Dict[str, Any]]:
    """One scheduled task (persisted + live state), or None if unknown."""
    doc = await tasks_store.get(task_id)
    live = await get_scheduler().get_task_status(task_id)
    if doc is None and live is None:
        return None
    return _merge_live(doc or {}, live)


async def delete_scheduled_task(task_id: str) -> bool:
    """Remove a task from the scheduler and the store. Returns False if it never existed."""
    removed = await get_scheduler().remove_task(task_id)
    deleted = await tasks_store.delete(task_id)
    return removed or deleted


async def restore_scheduled_tasks() -> int:
    """Re-register persisted tasks with the in-process scheduler after a restart."""
    scheduler = get_scheduler()
    restored = 0
    for doc in await tasks_store.find({"enabled": True, "status": "scheduled"}):
        task_data = doc.get("task_data") or {}
        try:
            next_run = datetime.fromisoformat(doc["next_run"]) if doc.get("next_run") else None
            await scheduler.schedule_interval(
                task_data,
                doc.get("interval_hours") or task_data.get("interval") or get_trinn_config()["default_interval_hours"],
                task_id=doc["task_id"],
                next_run=next_run,
            )
            restored += 1
        except Exception as e:
            logger.error(f"Failed to restore scheduled task {doc.get('task_id')}: {e}")
    if restored:
        logger.info(f"Restored {restored} scheduled trinn tasks")
    return restored


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
