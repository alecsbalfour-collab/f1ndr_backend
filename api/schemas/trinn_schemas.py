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
    region: Optional[str] = Field(None, max_length=50)


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


class ScheduledTaskOut(Record):
    """A scheduled trinn task: persisted fields plus live scheduler state when running."""
    task_id: str
    task: Optional[str] = None
    task_data: Optional[Dict[str, Any]] = None
    interval_hours: Optional[int] = None
    next_run: Optional[str] = None
    last_run: Optional[str] = None
    run_count: int = 0
    last_error: Optional[str] = None
    enabled: bool = True
    status: Optional[str] = None
    created_at: Optional[str] = None


class SchedulerStatus(Record):
    """In-process scheduler state and counters (see trinn.utils.scheduler.get_scheduler_state)."""
    status: str
    dead_tasks: Optional[int] = None
    total_scheduled_tasks: int = 0
    active_tasks: int = 0
    completed_runs: int = 0
    failed_runs: int = 0
    average_run_time_ms: float = 0.0
    success_rate: float = 0.0


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


# ---- Trinn AI brain ----

MemoryKind = Literal["lesson", "correction", "fact", "preference"]
MemoryTopic = Literal["general", "pricing", "fraud", "vehicles", "rvs", "copywriting", "operations"]
SessionMode = Literal["assistant", "mentor"]


class MemoryCreate(BaseModel):
    kind: MemoryKind = "lesson"
    topic: MemoryTopic = "general"
    content: str = Field(..., min_length=1, max_length=4000)
    context: Optional[str] = Field(None, max_length=2000)
    weight: int = Field(5, ge=1, le=10)


class MemoryOut(Record):
    id: Optional[str] = None
    kind: Optional[str] = None
    topic: Optional[str] = None
    content: Optional[str] = None
    context: Optional[str] = None
    weight: Optional[int] = None
    author_id: Optional[str] = None
    use_count: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: Optional[str] = None
    mode: SessionMode = "assistant"
    teach: bool = False


class MessageOut(Record):
    id: Optional[str] = None
    role: Optional[str] = None
    content: Optional[str] = None
    timestamp: Optional[str] = None
    tool_calls: Optional[List[str]] = None
    memories_used: Optional[List[str]] = None
    feedback: Optional[str] = None


class SessionOut(Record):
    id: Optional[str] = None
    user_id: Optional[str] = None
    title: Optional[str] = None
    mode: Optional[str] = None
    messages: Optional[List[MessageOut]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ChatResponse(Record):
    session_id: str
    reply: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    memories_used: Optional[List[MemoryOut]] = None
    learned_memory: Optional[MemoryOut] = None


class FeedbackRequest(BaseModel):
    session_id: str
    message_id: str
    rating: Literal["up", "down"]
    correction: Optional[str] = Field(None, max_length=4000)


class FeedbackResult(Record):
    recorded: bool
    learned_memory: Optional[MemoryOut] = None


class TrinnBrainStats(Record):
    total_memories: int
    memories_by_topic: Dict[str, int]
    total_sessions: int
    total_recalls: int
    llm_provider: Optional[str] = None
