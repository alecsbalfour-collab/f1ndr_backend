# f1ndr-backend/api/routes/scraper_routes.py
"""
Scraper API: platform list and multi-platform search. Scraper health is reported by /health.
"""

import logging
from typing import List

from fastapi import APIRouter, Depends

from api.dependencies.auth import require_scopes
from api.schemas.common import Envelope, ok
from api.schemas.scraper_schemas import ScrapeRequest, ScrapeSummary
from scrapers.module import SCRAPER_CLASSES, run_all


logger = logging.getLogger(__name__)

router = APIRouter(tags=["scrapers"])


@router.get("/platforms", response_model=Envelope[List[str]])
async def list_platforms():
    return ok(list(SCRAPER_CLASSES), "Supported scraper platforms")


# Admin-only: each call launches headless browsers against third-party sites.
@router.post("/search", response_model=Envelope[ScrapeSummary], dependencies=[Depends(require_scopes("tasks:admin"))])
async def scrapers_search(request: ScrapeRequest):
    data = await run_all(request.query, request.platforms)
    logger.info("Scrape '%s': %d listings, failed=%s", request.query, data["total"], data["failed"])
    return ok(data, f"Found {data['total']} listings")
