"""In-process trinn scheduler stopgap: lifespan startup runs due tasks, shutdown stops it."""

import asyncio
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI

from api.shutdown import on_shutdown
from api.startup import on_startup
from trinn.utils.scheduler import get_scheduler, get_scheduler_state


async def test_scheduler_runs_due_tasks_after_startup():
    app = FastAPI()
    # Keep the test hermetic: pretend Mongo is unavailable so startup doesn't
    # touch a real database; the scheduler doesn't need one anyway.
    with patch("api.startup.connect_to_db", new=AsyncMock(return_value=False)):
        await on_startup(app)
    try:
        assert get_scheduler_state()["status"] == "running"

        ran = asyncio.Event()

        async def fake_run(data):
            ran.set()
            return {"ok": True}

        scheduler = get_scheduler()
        # interval_hours=0 -> due on the scheduler loop's first check
        task_id = await scheduler.schedule_interval({"task": "vin", "vin": "X" * 17}, 0)

        with patch("trinn.core.core.run_task", side_effect=fake_run):
            await asyncio.wait_for(ran.wait(), timeout=5)
        assert scheduler.scheduled_tasks[task_id].run_count == 1
    finally:
        await on_shutdown(app)
        assert get_scheduler_state()["status"] == "stopped"


async def test_scheduler_not_started_with_multiple_workers(monkeypatch):
    monkeypatch.setenv("WORKERS", "4")
    from api.config.settings_config import get_settings
    get_settings.cache_clear()
    try:
        with patch("api.startup.connect_to_db", new=AsyncMock(return_value=False)):
            await on_startup(FastAPI())
        assert get_scheduler_state()["status"] in ("not_started", "stopped")
    finally:
        get_settings.cache_clear()
