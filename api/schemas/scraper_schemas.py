"""Scraper search models."""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from scrapers.base_scraper import MAX_QUERY_LENGTH
from scrapers.module import SCRAPER_CLASSES

ScraperPlatform = Literal[tuple(SCRAPER_CLASSES)]


class ScrapeRequest(BaseModel):
    query: Optional[str] = Field(None, max_length=MAX_QUERY_LENGTH)
    platforms: Optional[List[ScraperPlatform]] = None
    region: Optional[str] = Field(None, max_length=50)


class RegionInfo(BaseModel):
    slug: str
    label: str
    province: str
    platforms: List[str]


class ScrapeResult(BaseModel):
    source: str
    query: Optional[str] = None
    region: Optional[str] = None
    url: Optional[str] = None
    success: bool
    results: List[Dict[str, Any]]
    count: int
    error: Optional[str] = None
    cached: bool
    duration_ms: float
    scraped_at: str


class ScrapeSummary(BaseModel):
    query: Optional[str] = None
    region: Optional[str] = None
    platforms: List[str]
    total: int
    failed: List[str]
    results: Dict[str, ScrapeResult]
