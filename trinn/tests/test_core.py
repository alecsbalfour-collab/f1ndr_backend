"""
Tests for trinn.
"""

import pytest

from trinn.core.core import run_task, schedule_task
from trinn.core.exceptions_core import TrinnError


async def test_run_vin_task():
    result = await run_task({"task": "vin", "vin": "TESTVIN123"})
    assert result["status"] == "completed"
    assert result["result"]["valid"] is False


async def test_run_unknown_task_raises():
    with pytest.raises(TrinnError):
        await run_task({"task": "nope"})


async def test_schedule_task_in_memory():
    result = await schedule_task({"task": "vin", "vin": "TESTVIN123", "interval": 2})
    assert result["scheduled"] is True
    assert result["interval_hours"] == 2
    assert result["task_id"]
