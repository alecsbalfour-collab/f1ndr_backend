# f1ndr-backend/api/routes/controllers/health_controller.py
"""
DICT-aligned health controller with FlutterFlow compatibility and enterprise features.
"""

import logging
from fastapi import APIRouter
from utils.response_builder import success_response


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
async def health_check():
    """
    Health check endpoint with FlutterFlow-compatible response.
    
    Returns:
        FlutterFlow-compatible health status
    """
    try:
        # No DB calls, no external services — just a heartbeat.
        return success_response(
            data={
                "status": "ok",
                "service": "f1ndr-backend",
                "timestamp": _get_timestamp(),
            },
            message="Service is healthy"
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "error",
            "message": str(e),
            "timestamp": _get_timestamp(),
        }


def _get_timestamp():
    """Get current timestamp in ISO format."""
    from datetime import datetime
    return datetime.utcnow().isoformat()
