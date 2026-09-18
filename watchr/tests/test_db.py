# f1ndr-backend/watchr/tests/test_db.py
import pytest
from watchr.db.event_log_repo import EventLogRepo


class FakeClient:
    def __getitem__(self, name):
        return self

    async def insert_one(self, doc):
        pass

    def find(self, query):
        async def gen():
            yield {"ok": True}
        return gen()


@pytest.mark.asyncio
async def test_event_log_repo():
    repo = EventLogRepo(FakeClient())
    await repo.insert({"test": True})
    results = await repo.fetch({})
    assert results
