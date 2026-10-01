"""Liveness/readiness endpoints."""

import asyncio
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from pymongo.errors import ServerSelectionTimeoutError

from api.main import app
from api.routes.controllers import health_controller
from trinn.utils import scheduler as scheduler_mod

client = TestClient(app)


class FakeDatabase:
    def __init__(self, error=None):
        self.error = error

    async def command(self, name):
        assert name == "ping"
        if self.error:
            raise self.error
        return {"ok": 1}


@pytest.fixture
def deps(monkeypatch):
    """Control the Mongo handle, mongodb_required and scheduler state seen by the health controller."""
    state = SimpleNamespace(db=None, required=False, scheduler={"status": "not_started"})
    monkeypatch.setattr(health_controller, "get_database", lambda: state.db)
    monkeypatch.setattr(health_controller, "get_settings", lambda: SimpleNamespace(mongodb_required=state.required))
    monkeypatch.setattr(health_controller, "get_scheduler_state", lambda: state.scheduler)
    return state


def test_live_is_always_ok(deps):
    deps.db = FakeDatabase(error=ServerSelectionTimeoutError("down"))
    for path in ("/health/live", "/health/"):
        response = client.get(path)
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "ok"


def test_ready_with_in_memory_storage_when_mongo_optional(deps):
    response = client.get("/health/ready")
    assert response.status_code == 200
    checks = response.json()["data"]["checks"]
    assert checks["mongo"]["status"] == "disabled"
    assert checks["scheduler"]["status"] == "not_started"


def test_not_ready_when_mongo_required_but_not_connected(deps):
    deps.required = True
    response = client.get("/health/ready")
    assert response.status_code == 503
    body = response.json()
    assert body["success"] is False and body["error_code"] == "NOT_READY"
    assert body["details"]["checks"]["mongo"]["status"] == "unavailable"


def test_ready_when_mongo_pings(deps):
    deps.db = FakeDatabase()
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json()["data"]["checks"]["mongo"]["status"] == "ok"


def test_not_ready_when_mongo_ping_fails(deps):
    deps.db = FakeDatabase(error=ServerSelectionTimeoutError("secret-host:27017 refused"))
    response = client.get("/health/ready")
    assert response.status_code == 503
    assert response.json()["details"]["checks"]["mongo"]["status"] == "unreachable"
    assert "secret-host" not in response.text


def test_not_ready_when_scheduler_failed(deps):
    deps.scheduler = {"status": "failed", "dead_tasks": 1}
    response = client.get("/health/ready")
    assert response.status_code == 503
    assert response.json()["details"]["checks"]["scheduler"]["ok"] is False


async def test_scheduler_state_transitions(monkeypatch):
    monkeypatch.setattr(scheduler_mod, "_scheduler", None)
    assert scheduler_mod.get_scheduler_state() == {"status": "not_started"}

    scheduler = scheduler_mod.get_scheduler()
    assert scheduler_mod.get_scheduler_state()["status"] == "stopped"

    await scheduler.start(num_workers=1)
    try:
        assert scheduler_mod.get_scheduler_state()["status"] == "running"
        scheduler.worker_tasks[0].cancel()
        await asyncio.sleep(0)
        assert scheduler_mod.get_scheduler_state()["status"] == "failed"
    finally:
        await scheduler.stop()
    assert scheduler_mod.get_scheduler_state()["status"] == "stopped"
