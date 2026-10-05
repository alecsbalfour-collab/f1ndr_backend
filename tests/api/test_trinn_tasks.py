"""Scheduled-task management endpoints: list, get, delete, scheduler state, persistence."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.main import app
from api.router_api import API_V1_PREFIX
from api.startup import on_startup
from api.shutdown import on_shutdown
from trinn.core.core import delete_scheduled_task, restore_scheduled_tasks, schedule_task
from trinn.db.trinn_repo import tasks_store
from trinn.utils.scheduler import get_scheduler

VIN = "1HGCM82633A004352"


@pytest.fixture
def client():
    return TestClient(app)


def test_schedule_via_api_then_get_and_delete(client, headers_for):
    admin = headers_for("admin")
    created = client.post(
        f"{API_V1_PREFIX}/trinn/schedule",
        json={"task": "vin", "vin": VIN, "interval": 3},
        headers=admin,
    )
    assert created.status_code == 200
    task_id = created.json()["data"]["task_id"]

    try:
        got = client.get(f"{API_V1_PREFIX}/trinn/tasks/{task_id}", headers=admin)
        assert got.status_code == 200
        data = got.json()["data"]
        assert data["task"] == "vin" and data["interval_hours"] == 3
        assert data["enabled"] is True and data["next_run"]
    finally:
        deleted = client.delete(f"{API_V1_PREFIX}/trinn/tasks/{task_id}", headers=admin)
        assert deleted.status_code == 200

    assert client.get(f"{API_V1_PREFIX}/trinn/tasks/{task_id}", headers=admin).status_code == 404
    assert client.delete(f"{API_V1_PREFIX}/trinn/tasks/{task_id}", headers=admin).status_code == 404


async def test_list_tasks_includes_scheduled(client, headers_for):
    task_id = (await schedule_task({"task": "vin", "vin": VIN, "interval": 5}))["task_id"]
    try:
        listed = client.get(f"{API_V1_PREFIX}/trinn/tasks", headers=headers_for("admin"))
        assert listed.status_code == 200
        body = listed.json()
        ids = [t["task_id"] for t in body["data"]]
        assert task_id in ids
        assert body["pagination"]["total"] >= 1
    finally:
        await delete_scheduled_task(task_id)


def test_task_endpoints_require_admin(client, headers_for):
    assert client.get(f"{API_V1_PREFIX}/trinn/tasks").status_code == 401
    assert client.get(f"{API_V1_PREFIX}/trinn/tasks", headers=headers_for("dealer")).status_code == 403
    assert client.get(f"{API_V1_PREFIX}/trinn/scheduler", headers=headers_for("user")).status_code == 403
    assert client.delete(f"{API_V1_PREFIX}/trinn/tasks/abc", headers=headers_for("dealer")).status_code == 403


def test_run_scrape_failure_returns_502(client, headers_for, monkeypatch):
    """A failed task execution surfaces as 502 TASK_FAILED-ish error, not a bare 500."""
    import trinn.core.core as core

    monkeypatch.setattr(core, "run_scraper", AsyncMock(return_value={"success": False, "error": "blocked"}))
    resp = client.post(
        f"{API_V1_PREFIX}/trinn/run",
        json={"task": "scrape", "platform": "kijiji"},
        headers=headers_for("admin"),
    )
    assert resp.status_code == 502
    body = resp.json()
    assert body["success"] is False and body["error_code"] == "TRINN_ERROR"
    assert "blocked" in body["details"]["reason"]


def test_scheduler_status_endpoint(client, headers_for):
    resp = client.get(f"{API_V1_PREFIX}/trinn/scheduler", headers=headers_for("admin"))
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] in ("running", "stopped", "not_started", "failed")


async def test_persisted_tasks_restore_on_startup():
    """A task in the store is re-registered with the scheduler by startup."""
    task_id = (await schedule_task({"task": "vin", "vin": VIN, "interval": 5}))["task_id"]
    scheduler = get_scheduler()
    try:
        await scheduler.remove_task(task_id)  # simulate restart losing in-memory state
        assert scheduler.scheduled_tasks.get(task_id) is None

        app2 = FastAPI()
        try:
            with patch("api.startup.connect_to_db", new=AsyncMock(return_value=False)):
                await on_startup(app2)
            assert scheduler.scheduled_tasks.get(task_id) is not None
            assert scheduler.scheduled_tasks[task_id].interval_hours == 5
        finally:
            await on_shutdown(app2)
    finally:
        await delete_scheduled_task(task_id)


async def test_deleted_task_not_restored():
    task_id = (await schedule_task({"task": "vin", "vin": VIN, "interval": 2}))["task_id"]
    assert await delete_scheduled_task(task_id)
    assert await tasks_store.get(task_id) is None
    await restore_scheduled_tasks()
    assert get_scheduler().scheduled_tasks.get(task_id) is None
