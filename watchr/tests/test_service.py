# f1ndr-backend/watchr/tests/test_service.py
import pytest
from watchr.core.service_core import WatchrService


class FakeRepo:
    async def insert(self, doc):
        pass

    async def fetch(self, query):
        return []


@pytest.mark.asyncio
async def test_service_process():
    service = WatchrService(FakeRepo(), FakeRepo(), FakeRepo(), FakeRepo())
    result = await service.process({"event_type": "test", "timestamp": 1})
    assert "event" in result
