# f1ndr-backend/watchr/tests/test_controller.py
import pytest
from watchr.module import WatchrModule


@pytest.mark.asyncio
async def test_controller_process():
    module = WatchrModule("mongodb://localhost:27017")
    controller = module.get_controller()
    result = await controller.process({"event_type": "test", "timestamp": 1})
    assert "event" in result
