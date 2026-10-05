# f1ndr-backend/api/routes/trinn_routes.py
"""
DICT-aligned TRINN API routes with enterprise features.
"""

from fastapi import APIRouter, Depends, Query, Request
import logging
from typing import Any, Dict

from api.auth.audit import record_audit
from api.dependencies.auth import require_scopes
from api.schemas.common import Envelope, ModuleStatus, Page, error_responses, ok, paged
from api.schemas.trinn_schemas import (
    ScheduleResult,
    ScheduledTaskOut,
    SchedulerStatus,
    TaskResult,
    TrinnConfig,
    TrinnTask,
)
from trinn.core import core as trinn_core
from trinn.module import TrinnModule
from trinn.config.config import get_trinn_config
from trinn.utils.scheduler import get_scheduler_state
from utils.response_builder import error_response


logger = logging.getLogger(__name__)

router = APIRouter(tags=["trinn"])

_ADMIN = [Depends(require_scopes("tasks:admin"))]

# Initialize TRINN module
trinn_module = TrinnModule()


@router.get("/status", response_model=Envelope[ModuleStatus])
async def trinn_status():
    """
    Get TRINN module status with enterprise metadata.
    
    Returns:
        Dictionary with module status and configuration info
    """
    config = get_trinn_config()
    return ok(
        {
            "module": "trinn",
            "status": "operational",
            "feature_key": config["feature_key"],
            "feature_version": config["feature_version"],
            "enabled": config["enabled"],
            "config": {
                "enable_scraper_tasks": config["enable_scraper_tasks"],
                "enable_vin_tasks": config["enable_vin_tasks"],
                "enable_watchr_tasks": config["enable_watchr_tasks"],
                "enable_listing_sync": config["enable_listing_sync"],
                "default_interval_hours": config["default_interval_hours"],
            },
            "supported_platforms": config["supported_platforms"],
        },
        "TRINN module operational",
    )


@router.post("/run", response_model=Envelope[TaskResult])
async def trinn_run_task(
    task_data: TrinnTask,
    request: Request,
    claims: Dict[str, Any] = Depends(require_scopes("tasks:admin")),
):
    """
    Execute a TRINN task with enterprise error handling.

    Args:
        task_data: Task data containing task type and parameters

    Returns:
        Dictionary with task execution results
    """
    logger.info(f"Received TRINN run request: {task_data.task}")
    result = await trinn_module.run("run", task_data.model_dump(exclude_none=True))
    await record_audit("trinn_task_run", request, actor_id=claims["sub"], details={"task": task_data.task})
    logger.info("TRINN task executed successfully")
    return ok(result, "Task executed")


@router.post("/schedule", response_model=Envelope[ScheduleResult])
async def trinn_schedule_task(
    task_data: TrinnTask,
    request: Request,
    claims: Dict[str, Any] = Depends(require_scopes("tasks:admin")),
):
    """
    Schedule a TRINN task with enterprise scheduling logic.

    Args:
        task_data: Task data containing scheduling parameters

    Returns:
        Dictionary with scheduling confirmation
    """
    logger.info(f"Received TRINN schedule request: {task_data.task}")
    result = await trinn_module.run("schedule", task_data.model_dump(exclude_none=True))
    await record_audit(
        "trinn_task_scheduled", request, actor_id=claims["sub"],
        details={"task": task_data.task, "task_id": result["task_id"]},
    )
    logger.info("TRINN task scheduled successfully")
    return ok(result, "Task scheduled")


@router.get("/tasks", response_model=Page[ScheduledTaskOut], dependencies=_ADMIN, responses=error_responses(401, 403))
async def trinn_list_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List scheduled tasks: persisted records overlaid with live scheduler state."""
    tasks = await trinn_core.list_scheduled_tasks()
    start = (page - 1) * page_size
    return paged(tasks[start: start + page_size], len(tasks), page, page_size, "Scheduled tasks retrieved")


@router.get("/tasks/{task_id}", response_model=Envelope[ScheduledTaskOut], dependencies=_ADMIN, responses=error_responses(401, 403, 404))
async def trinn_get_task(task_id: str):
    """Get one scheduled task by ID."""
    task = await trinn_core.get_scheduled_task(task_id)
    if task is None:
        return error_response(message="Task not found", status_code=404, error_code="NOT_FOUND")
    return ok(task, "Scheduled task retrieved")


@router.delete("/tasks/{task_id}", response_model=Envelope[None], responses=error_responses(401, 403, 404))
async def trinn_delete_task(
    task_id: str,
    request: Request,
    claims: Dict[str, Any] = Depends(require_scopes("tasks:admin")),
):
    """Cancel and remove a scheduled task."""
    logger.info(f"Deleting scheduled task: {task_id}")
    if not await trinn_core.delete_scheduled_task(task_id):
        return error_response(message="Task not found", status_code=404, error_code="NOT_FOUND")
    await record_audit("trinn_task_deleted", request, actor_id=claims["sub"], details={"task_id": task_id})
    return ok(message="Scheduled task deleted")


@router.get("/scheduler", response_model=Envelope[SchedulerStatus], dependencies=_ADMIN, responses=error_responses(401, 403))
async def trinn_scheduler_status():
    """In-process scheduler state and run counters."""
    return ok(get_scheduler_state(), "Scheduler status retrieved")


@router.get("/config", response_model=Envelope[TrinnConfig], dependencies=_ADMIN)
async def trinn_get_config():
    """
    Get current TRINN configuration.
    
    Returns:
        Dictionary with current configuration
    """
    return ok(get_trinn_config(), "TRINN configuration retrieved")
