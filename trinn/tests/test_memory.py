"""Unit tests for trinn long-term memory (teach / recall / list / delete)."""

import pytest


@pytest.fixture(autouse=True)
def clean():
    from trinn.db.trinn_repo import memories_store, sessions_store
    memories_store.clear_memory()
    sessions_store.clear_memory()


async def test_teach_memory_creates_doc():
    from trinn.core.memory_core import teach_memory
    m = await teach_memory({"kind": "lesson", "topic": "pricing",
                            "content": "RVs depreciate slower than cars", "weight": 7},
                           author_id="u1")
    assert m["kind"] == "lesson" and m["topic"] == "pricing"
    assert m["weight"] == 7 and m["use_count"] == 0 and m["author_id"] == "u1"


async def test_recall_ranks_and_increments_use_count():
    from trinn.core.memory_core import teach_memory, recall_memories
    weak = await teach_memory({"topic": "general", "content": "honda civic info", "weight": 1}, "u")
    strong = await teach_memory({"topic": "vehicles", "content": "honda civic trims", "weight": 9}, "u")
    out = await recall_memories("honda civic")
    assert out[0]["id"] == strong["id"] and out[0]["use_count"] == 1
    out2 = await recall_memories("honda civic")
    assert out2[0]["use_count"] == 2


async def test_recall_topic_filter():
    from trinn.core.memory_core import teach_memory, recall_memories
    await teach_memory({"topic": "general", "content": "generic note"}, "u")
    rv = await teach_memory({"topic": "rvs", "content": "fifth wheel weight rules"}, "u")
    out = await recall_memories("anything", topic="rvs")
    assert [m["id"] for m in out] == [rv["id"]]


async def test_list_delete_and_bump_weight():
    from trinn.core.memory_core import bump_weight, delete_memory, list_memories, teach_memory
    a = await teach_memory({"content": "a", "kind": "fact", "topic": "fraud"}, "u")
    await teach_memory({"content": "b", "kind": "lesson", "topic": "general"}, "u")
    assert (await list_memories())["total"] == 2
    assert (await list_memories(kind="fact"))["items"][0]["id"] == a["id"]
    assert (await list_memories(topic="general"))["total"] == 1
    await bump_weight(a["id"], 3)
    assert (await list_memories(kind="fact"))["items"][0]["weight"] == 8
    assert await delete_memory(a["id"])
    assert not await delete_memory("missing")
    assert (await list_memories())["total"] == 1
