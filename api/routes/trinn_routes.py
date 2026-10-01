# f1ndr-backend/api/routes/trinn_routes.py
"""
DICT-aligned TRINN API routes with enterprise features.
"""

from fastapi import APIRouter, Depends
import logging

from api.dependencies.auth import require_scopes
from api.schemas.common import Envelope, ModuleStatus, ok
from api.schemas.trinn_schemas import ScheduleResult, TaskResult, TrinnConfig, TrinnTask
from trinn.module import TrinnModule
from trinn.config.config import get_trinn_config


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


@router.post("/run", response_model=Envelope[TaskResult], dependencies=_ADMIN)
async def trinn_run_task(task_data: TrinnTask):
    """
    Execute a TRINN task with enterprise error handling.
    
    Args:
        task_data: Task data containing task type and parameters
        
    Returns:
        Dictionary with task execution results
    """
    logger.info(f"Received TRINN run request: {task_data.task}")
    result = await trinn_module.run("run", task_data.model_dump(exclude_none=True))
    logger.info("TRINN task executed successfully")
    return ok(result, "Task executed")


@router.post("/schedule", response_model=Envelope[ScheduleResult], dependencies=_ADMIN)
async def trinn_schedule_task(task_data: TrinnTask):
    """
    Schedule a TRINN task with enterprise scheduling logic.
    
    Args:
        task_data: Task data containing scheduling parameters
        
    Returns:
        Dictionary with scheduling confirmation
    """
    logger.info(f"Received TRINN schedule request: {task_data.task}")
    result = await trinn_module.run("schedule", task_data.model_dump(exclude_none=True))
    logger.info("TRINN task scheduled successfully")
    return ok(result, "Task scheduled")


@router.get("/config", response_model=Envelope[TrinnConfig], dependencies=_ADMIN)
async def trinn_get_config():
    """
    Get current TRINN configuration.
    
    Returns:
        Dictionary with current configuration
    """
    return ok(get_trinn_config(), "TRINN configuration retrieved")
