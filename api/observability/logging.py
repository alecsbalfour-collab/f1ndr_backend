"""Structured JSON logging with request/trace correlation via ContextVars."""

import json
import logging
import re
import traceback
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Optional, Tuple

request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
trace_id_var: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)
span_id_var: ContextVar[Optional[str]] = ContextVar("span_id", default=None)

_TRACEPARENT = re.compile(r"^[\da-f]{2}-([\da-f]{32})-([\da-f]{16})-[\da-f]{2}$")

_EXTRA_KEYS = ("method", "path", "status_code", "duration_ms")


def parse_traceparent(header: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """W3C traceparent `version-traceid-spanid-flags` -> (trace_id, span_id)."""
    if not header:
        return None, None
    m = _TRACEPARENT.match(header.strip().lower())
    return (m.group(1), m.group(2)) if m else (None, None)


class JsonLogFormatter(logging.Formatter):
    """Single-line JSON records; request/trace ids come from the ContextVars."""

    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        rid = request_id_var.get()
        if rid:
            entry["request_id"] = rid
        tid, sid = trace_id_var.get(), span_id_var.get()
        if tid:
            entry["trace_id"] = tid
        if sid:
            entry["span_id"] = sid
        for key in _EXTRA_KEYS:
            value = getattr(record, key, None)
            if value is not None:
                entry[key] = value
        if record.exc_info:
            entry["exception"] = "".join(traceback.format_exception(*record.exc_info)).rstrip()
        return json.dumps(entry, default=str)


def configure_logging() -> None:
    """Apply settings-driven format/level to the root logger."""
    from api.config.settings_config import get_settings

    settings = get_settings()
    level = getattr(logging, str(settings.LOG_LEVEL).upper(), logging.INFO)
    logging.basicConfig(level=level, force=True)
    if getattr(settings, "LOG_FORMAT", "json") == "json":
        formatter = JsonLogFormatter()
        for handler in logging.getLogger().handlers:
            handler.setFormatter(formatter)
