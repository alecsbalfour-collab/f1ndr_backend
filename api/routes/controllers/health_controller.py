# f1ndr-backend/api/routes/controllers/health_controller.py
"""
DICT-aligned health controller with FlutterFlow compatibility and enterprise features.
`/health` reports module/scraper state as components; `/health/live` and `/health/ready`
are the liveness and readiness probes for Docker and load balancers.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Tuple

from fastapi import APIRouter
from pydantic import BaseModel

from api.config.settings_config import get_settings
from api.schemas.common import Envelope, ErrorEnvelope, ok
from api.security.rate_limiter import limiter
from db.connection_db import get_database
from scrapers.module import health_report
from trinn.config.config import get_trinn_config
from trinn.utils.scheduler import get_scheduler_state
from utils.response_builder import error_response, success_response


logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])

MONGO_PING_TIMEOUT_SECONDS = 2.0


class Liveness(BaseModel):
    status: str


class Readiness(BaseModel):
    status: str
    checks: Dict[str, Dict[str, Any]]


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


@router.get("/health/live", response_model=Envelope[Liveness])
@router.get("/health/", response_model=Envelope[Liveness], include_in_schema=False)
@limiter.exempt
async def liveness():
    """The process is up and serving requests. Never checks dependencies, so it can't cause restart loops."""
    return ok({"status": "ok"}, "Alive")


async def _mongo_check() -> Dict[str, Any]:
    database = get_database()
    if database is None:
        # In-memory storage is a valid state unless Mongo is required (production)
        if get_settings().mongodb_required:
            return {"status": "unavailable", "ok": False}
        return {"status": "disabled", "ok": True}
    try:
        await asyncio.wait_for(database.command("ping"), MONGO_PING_TIMEOUT_SECONDS)
    except Exception as exc:
        # Log the cause server-side only; it can contain hostnames
        logger.warning("Readiness: Mongo ping failed: %s", exc)
        return {"status": "unreachable", "ok": False}
    return {"status": "ok", "ok": True}


def _scheduler_check() -> Dict[str, Any]:
    state = get_scheduler_state()
    return {**state, "ok": state["status"] != "failed"}


async def readiness_report() -> Tuple[bool, Dict[str, Dict[str, Any]]]:
    checks = {"mongo": await _mongo_check(), "scheduler": _scheduler_check()}
    return all(check["ok"] for check in checks.values()), checks


@router.get("/health/ready", response_model=Envelope[Readiness],
            responses={503: {"model": ErrorEnvelope, "description": "A dependency is not ready"}})
@limiter.exempt
async def readiness():
    """Ready to take traffic: Mongo reachable (when connected or required) and scheduler workers alive."""
    ready, checks = await readiness_report()
    if not ready:
        return error_response(message="Service not ready", status_code=503, error_code="NOT_READY",
                              details={"checks": checks})
    return ok({"status": "ready", "checks": checks}, "Ready")
