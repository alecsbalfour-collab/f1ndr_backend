"""TRINN task models. `task` selects the variant; `interval` is only used by /trinn/schedule."""

from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field
from typing_extensions import Annotated

from api.schemas.common import VIN, Record
from api.schemas.list_schemas import ListrPlatform
from api.schemas.scraper_schemas import ScraperPlatform
from scrapers.base_scraper import MAX_QUERY_LENGTH


class _Task(BaseModel):
    interval: Optional[int] = Field(None, ge=1, description="Hours between runs (schedule only)")


class ScrapeTask(_Task):
    task: Literal["scrape"]
    platform: ScraperPlatform
    query: Optional[str] = Field(None, max_length=MAX_QUERY_LENGTH)


class VinTask(_Task):
    task: Literal["vin"]
    vin: VIN


class SyncTask(_Task):
    task: Literal["sync"]
    platform: ListrPlatform
    listing: Dict[str, Any] = Field(..., min_length=1)


TrinnTask = Annotated[Union[ScrapeTask, VinTask, SyncTask], Field(discriminator="task")]


class TaskResult(Record):
    task: str
    status: str
    timestamp: str
    result: Optional[Any] = None
    module_metadata: Dict[str, Any]


class ScheduleResult(Record):
    scheduled: bool
    task_id: str
    interval_hours: int
    next_run: str
    status: str
    timestamp: str
    module_metadata: Dict[str, Any]


class TrinnConfig(BaseModel):
    feature_key: str
    feature_version: str
    enabled: bool
    enable_scraper_tasks: bool
    enable_vin_tasks: bool
    enable_watchr_tasks: bool
    enable_listing_sync: bool
    default_interval_hours: int
    max_retries: int
    retry_delay: float
    batch_size: int
    supported_platforms: List[str]
