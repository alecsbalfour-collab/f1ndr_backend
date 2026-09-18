# f1ndr-backend/api/routes/controllers/version_controller.py
"""
DICT-aligned version controller with FlutterFlow compatibility and enterprise features.
"""

import logging
from fastapi import APIRouter
from utils.response_builder import success_response


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/version", tags=["version"])


@router.get("/")
async def version_info():
    """
    Version information endpoint with FlutterFlow-compatible response.
    
    Returns:
        FlutterFlow-compatible version information
    """
    try:
        return success_response(
            data={
                "version": "1.0.0",
                "description": "F1NDR Backend API",
                "status": "stable",
                "api_type": "REST",
                "flutterflow_compatible": True,
                "enterprise_features": True,
                "timestamp": _get_timestamp(),
            },
            message="Version information retrieved"
        )
        
    except Exception as e:
        logger.error(f"Version info failed: {e}")
        return {
            "version": "unknown",
            "status": "error",
            "message": str(e),
            "timestamp": _get_timestamp(),
        }


def _get_timestamp():
    """Get current timestamp in ISO format."""
    from datetime import datetime
    return datetime.utcnow().isoformat()
