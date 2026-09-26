# f1ndr-backend/trinn/tests/test_handle.py
import pytest
from trinn.core.controller_core import TrinnController
from trinn.core.service_core import TrinnService


class FakeRepo:
    def __init__(self):
        self.docs = []

    async def insert(self, doc):
        self.docs.append(doc)
        return str(len(self.docs))


@pytest.mark.asyncio
async def test_trinn_pipeline_handle():
    controller = TrinnController(TrinnService(FakeRepo(), FakeRepo(), FakeRepo(), FakeRepo()))
    result = await controller.run_pipeline({"task": "ingest", "source": "test", "raw": {"id": 1}})
    assert "enrich" in result
    assert "normalize" in result
    assert "transform" in result
