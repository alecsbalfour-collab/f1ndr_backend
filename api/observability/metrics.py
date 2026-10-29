"""In-process Prometheus-format metrics: HTTP counters/latency/active gauge,
plus scraper run/circuit counters from metrics_registry."""

import threading
from collections import defaultdict
from typing import Dict, Tuple

_lock = threading.Lock()
_http_requests: Dict[Tuple[str, str, int], int] = defaultdict(int)
_http_duration_sum: Dict[Tuple[str, str], float] = defaultdict(float)
_http_duration_count: Dict[Tuple[str, str], int] = defaultdict(int)
_active_requests = 0


def inc_active() -> None:
    global _active_requests
    with _lock:
        _active_requests += 1


def dec_active() -> None:
    global _active_requests
    with _lock:
        _active_requests -= 1


def record_request(method: str, path: str, status_code: int, duration_ms: float) -> None:
    with _lock:
        _http_requests[(method, path, status_code)] += 1
        _http_duration_sum[(method, path)] += duration_ms / 1000.0
        _http_duration_count[(method, path)] += 1


def _esc(value) -> str:
    return str(value).replace("\\", "\\\\").replace('"', '\\"')


def render_prometheus() -> str:
    lines = [
        "# HELP http_requests_total HTTP requests by method, route, status.",
        "# TYPE http_requests_total counter",
    ]
    with _lock:
        items = list(_http_requests.items())
        sums = dict(_http_duration_sum)
        counts = dict(_http_duration_count)
        active = _active_requests
    for (method, path, status), n in sorted(items):
        lines.append(
            f'http_requests_total{{method="{_esc(method)}",path="{_esc(path)}",'
            f'status_code="{status}"}} {n}'
        )
    lines += [
        "# HELP http_request_duration_seconds Request latency.",
        "# TYPE http_request_duration_seconds summary",
    ]
    for (method, path), total in sorted(sums.items()):
        labels = f'method="{_esc(method)}",path="{_esc(path)}"'
        lines.append(f"http_request_duration_seconds_sum{{{labels}}} {total:.6f}")
        lines.append(f"http_request_duration_seconds_count{{{labels}}} {counts[(method, path)]}")
    lines += [
        "# HELP http_requests_active In-flight requests.",
        "# TYPE http_requests_active gauge",
        f"http_requests_active {active}",
        "# HELP scraper_runs_total Scraper runs by result.",
        "# TYPE scraper_runs_total counter",
        "# HELP scraper_rejected_total Scraper calls rejected by an open circuit.",
        "# TYPE scraper_rejected_total counter",
        "# HELP scraper_cache_hits_total Scraper cache hits.",
        "# TYPE scraper_cache_hits_total counter",
        "# HELP scraper_listings_total Listings scraped by platform.",
        "# TYPE scraper_listings_total counter",
    ]
    from scrapers.core.metrics_core import metrics_registry

    for source, snap in metrics_registry.snapshot().items():
        s = _esc(source)
        lines.append(f'scraper_runs_total{{source="{s}",result="success"}} {snap["successes"]}')
        lines.append(f'scraper_runs_total{{source="{s}",result="failure"}} {snap["failures"]}')
        lines.append(f'scraper_rejected_total{{source="{s}"}} {snap["rejected"]}')
        lines.append(f'scraper_cache_hits_total{{source="{s}"}} {snap["cache_hits"]}')
        lines.append(f'scraper_listings_total{{source="{s}"}} {snap["listings_total"]}')
    return "\n".join(lines) + "\n"
