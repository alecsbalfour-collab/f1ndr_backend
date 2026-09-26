# f1ndr-backend/api/routes/scraper_routes.py
"""
Scraper API: platform list, health (circuit state + metrics), and multi-platform search.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from scrapers.base_scraper import MAX_QUERY_LENGTH
from scrapers.module import SCRAPER_CLASSES, health_report, run_all
from utils.response_builder import error_response, success_response


logger = logging.getLogger(__name__)

router = APIRouter(tags=["scrapers"])


class ScrapeRequest(BaseModel):
    query: Optional[str] = Field(None, max_length=MAX_QUERY_LENGTH)
    platforms: Optional[List[str]] = None


@router.get("/platforms")
async def list_platforms():
    return success_response(data=list(SCRAPER_CLASSES), message="Supported scraper platforms")


@router.get("/health")
async def scrapers_health():
    report = health_report()
    return success_response(
        data=report,
        message=f"Scrapers {report['status']}",
        status_code=200 if report["status"] != "down" else 503,
    )


@router.post("/search")
async def scrapers_search(request: ScrapeRequest):
    try:
        data = await run_all(request.query, request.platforms)
    except ValueError as e:
        return error_response(message=str(e), status_code=400, error_code="UNSUPPORTED_PLATFORM")
    logger.info("Scrape '%s': %d listings, failed=%s", request.query, data["total"], data["failed"])
    return success_response(data=data, message=f"Found {data['total']} listings")
