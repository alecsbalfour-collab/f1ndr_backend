# f1ndr-backend/api/routes/trinn_routes.py
"""
DICT-aligned TRINN API routes with enterprise features.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
import logging

from trinn.module import TrinnModule
from trinn.config.config import get_trinn_config


logger = logging.getLogger(__name__)

router = APIRouter(tags=["trinn"])

# Initialize TRINN module
trinn_module = TrinnModule()


@router.get("/status")
async def trinn_status() -> Dict[str, Any]:
    """
    Get TRINN module status with enterprise metadata.
    
    Returns:
        Dictionary with module status and configuration info
    """
    try:
        config = get_trinn_config()
        
        return {
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
        }
        
    except Exception as e:
        logger.error(f"Failed to get TRINN status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.post("/run")
async def trinn_run_task(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a TRINN task with enterprise error handling.
    
    Args:
        task_data: Task data containing task type and parameters
        
    Returns:
        Dictionary with task execution results
    """
    try:
        logger.info(f"Received TRINN run request: {task_data.get('task', 'unknown')}")
        
        result = await trinn_module.run("run", task_data)
        
        logger.info("TRINN task executed successfully")
        return result
        
    except Exception as e:
        logger.error(f"TRINN task execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Task execution failed: {str(e)}")


@router.post("/schedule")
async def trinn_schedule_task(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Schedule a TRINN task with enterprise scheduling logic.
    
    Args:
        task_data: Task data containing scheduling parameters
        
    Returns:
        Dictionary with scheduling confirmation
    """
    try:
        logger.info(f"Received TRINN schedule request: {task_data.get('task', 'unknown')}")
        
        result = await trinn_module.run("schedule", task_data)
        
        logger.info("TRINN task scheduled successfully")
        return result
        
    except Exception as e:
        logger.error(f"TRINN task scheduling failed: {e}")
        raise HTTPException(status_code=500, detail=f"Task scheduling failed: {str(e)}")


@router.get("/config")
async def trinn_get_config() -> Dict[str, Any]:
    """
    Get current TRINN configuration.
    
    Returns:
        Dictionary with current configuration
    """
    try:
        config = get_trinn_config()
        
        return {
            "feature_key": config["feature_key"],
            "feature_version": config["feature_version"],
            "enabled": config["enabled"],
            "enable_scraper_tasks": config["enable_scraper_tasks"],
            "enable_vin_tasks": config["enable_vin_tasks"],
            "enable_watchr_tasks": config["enable_watchr_tasks"],
            "enable_listing_sync": config["enable_listing_sync"],
            "default_interval_hours": config["default_interval_hours"],
            "max_retries": config["max_retries"],
            "retry_delay": config["retry_delay"],
            "batch_size": config["batch_size"],
            "supported_platforms": config["supported_platforms"],
        }
        
    except Exception as e:
        logger.error(f"Failed to get TRINN config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get config: {str(e)}")


@router.get("/health")
async def trinn_health_check() -> Dict[str, Any]:
    """
    Health check endpoint for TRINN module.
    
    Returns:
        Dictionary with health status
    """
    try:
        config = get_trinn_config()
        
        return {
            "status": "healthy" if config["enabled"] else "disabled",
            "module": "trinn",
            "timestamp": _get_timestamp(),
        }
        
    except Exception as e:
        logger.error(f"TRINN health check failed: {e}")
        return {
            "status": "unhealthy",
            "module": "trinn",
            "error": str(e),
            "timestamp": _get_timestamp(),
        }


def _get_timestamp() -> str:
    """Get current timestamp in ISO format."""
    from datetime import datetime
    return datetime.utcnow().isoformat()
