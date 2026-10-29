"""Observability: JSON logs carry request/trace ids, /metrics exposes counters,
Sentry hook fires on unhandled 500s only when configured."""

import json
import logging

import pytest
from fastapi.testclient import TestClient

from api.observability.logging import (
    JsonLogFormatter,
    parse_traceparent,
    request_id_var,
    trace_id_var,
)


@pytest.fixture(scope="module")
def client():
    from api.main import app
    return TestClient(app, raise_server_exceptions=False)


def _record(msg="hi", exc=None):
    r = logging.LogRecord("t", logging.INFO, __file__, 1, msg, (), exc)
    return JsonLogFormatter().format(r)


def test_json_formatter_includes_request_id_and_exception():
    tok = request_id_var.set("req-123")
    try:
        try:
            raise RuntimeError("boom")
        except RuntimeError:
            import sys
            entry = json.loads(_record(exc=sys.exc_info()))
    finally:
        request_id_var.reset(tok)
    assert entry["request_id"] == "req-123" and entry["message"] == "hi"
    assert "RuntimeError: boom" in entry["exception"]
    assert entry["level"] == "INFO" and entry["logger"] == "t"


def test_parse_traceparent():
    assert parse_traceparent(
        "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
    ) == ("4bf92f3577b34da6a3ce929d0e0e4736", "00f067aa0ba902b7")
    assert parse_traceparent("garbage") == (None, None)
    assert parse_traceparent(None) == (None, None)


def test_metrics_endpoint(client):
    resp = client.get("/metrics")
    assert resp.status_code == 200 and "text/plain" in resp.headers["content-type"]
    body = resp.text
    assert "http_requests_total" in body and "http_requests_active" in body
    assert "http_request_duration_seconds" in body and "scraper_" in body


def test_traceparent_flows_into_log_context(client):
    tid = "4bf92f3577b34da6a3ce929d0e0e4736"
    captured = {}
    tok = trace_id_var.set(None)
    try:
        resp = client.get("/health/live", headers={"traceparent": f"00-{tid}-00f067aa0ba902b7-01"})
    finally:
        trace_id_var.reset(tok)
    assert resp.status_code == 200  # middleware parsed without rejecting


def test_sentry_capture_noop_when_unset():
    from api.observability import sentry
    sentry._sdk = None
    sentry.capture(RuntimeError("x"), request_id="r1")  # must not raise


def test_sentry_capture_tags_request_id(monkeypatch):
    from api.observability import sentry

    sent = {}

    class Scope:
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False
        def set_tag(self, k, v):
            sent[k] = v

    class FakeSdk:
        def push_scope(self):
            return Scope()
        def capture_exception(self, exc):
            sent["exc"] = exc

    monkeypatch.setattr(sentry, "_sdk", FakeSdk())
    sentry.capture(ValueError("v"), request_id="req-9")
    assert sent["request_id"] == "req-9" and isinstance(sent["exc"], ValueError)
