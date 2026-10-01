# f1ndr-backend/api/routes/controllers/version_controller.py
"""
DICT-aligned version controller with FlutterFlow compatibility and enterprise features.
"""

import logging
from fastapi import APIRouter
from api.schemas.common import Envelope, VersionInfo, ok


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/version", tags=["version"])


@router.get("/", response_model=Envelope[VersionInfo])
async def version_info():
    """
    Version information endpoint with FlutterFlow-compatible response.
    
    Returns:
        FlutterFlow-compatible version information
    """
    return ok(
        {
            "version": "1.0.0",
            "description": "F1NDR Backend API",
            "status": "stable",
            "api_type": "REST",
            "flutterflow_compatible": True,
            "enterprise_features": True,
            "timestamp": _get_timestamp(),
        },
        "Version information retrieved",
    )


def _get_timestamp():
    """Get current timestamp in ISO format."""
    from datetime import datetime
    return datetime.utcnow().isoformat()
