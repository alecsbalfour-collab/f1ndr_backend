# scrapers/core/metrics_core.py
"""
In-process run metrics per platform, exposed through the scraper health report.
"""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Dict


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ScraperMetrics:
    source: str
    successes: int = 0
    failures: int = 0
    rejected: int = 0
    cache_hits: int = 0
    listings_total: int = 0
    last_listing_count: int | None = None
    last_duration_ms: float | None = None
    last_error: str | None = None
    last_success_at: str | None = None
    last_failure_at: str | None = None

    def record_success(self, duration_ms: float, listing_count: int) -> None:
        self.successes += 1
        self.listings_total += listing_count
        self.last_listing_count = listing_count
        self.last_duration_ms = duration_ms
        self.last_success_at = _now()

    def record_failure(self, duration_ms: float, error: str) -> None:
        self.failures += 1
        self.last_duration_ms = duration_ms
        self.last_error = error
        self.last_failure_at = _now()

    def record_rejected(self) -> None:
        self.rejected += 1

    def record_cache_hit(self) -> None:
        self.cache_hits += 1

    def snapshot(self) -> dict:
        return asdict(self)


class MetricsRegistry:
    def __init__(self):
        self._metrics: Dict[str, ScraperMetrics] = {}

    def get(self, source: str) -> ScraperMetrics:
        return self._metrics.setdefault(source, ScraperMetrics(source))

    def snapshot(self) -> Dict[str, dict]:
        return {source: metrics.snapshot() for source, metrics in self._metrics.items()}

    def reset(self) -> None:
        self._metrics.clear()


metrics_registry = MetricsRegistry()
