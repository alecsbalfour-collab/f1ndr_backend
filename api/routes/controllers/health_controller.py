# f1ndr-backend/api/routes/controllers/health_controller.py
"""
DICT-aligned health controller with FlutterFlow compatibility and enterprise features.
The single health endpoint for the service; module/scraper state is reported as components.
"""

import logging
from datetime import datetime, timezone
from fastapi import APIRouter
from api.security.rate_limiter import limiter
from scrapers.module import health_report
from trinn.config.config import get_trinn_config
from utils.response_builder import success_response


logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health")
@limiter.exempt
async def health_check():
    """
    Health check endpoint with FlutterFlow-compatible response.
    
    Returns:
        FlutterFlow-compatible health status
    """
    # No DB calls, no external services — in-process state only.
    return success_response(
        data={
            "status": "ok",
            "service": "f1ndr-backend",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "components": {
                "trinn": "enabled" if get_trinn_config()["enabled"] else "disabled",
                "scrapers": health_report(),
            },
        },
        message="Service is healthy"
    )
