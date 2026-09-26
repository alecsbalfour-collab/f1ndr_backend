"""
Storage layer tests: DocumentStore behaviour (in-memory and, when available,
MongoDB) plus app startup/shutdown wiring.
"""

import os
import uuid

import pytest
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from api.config.settings_config import get_settings
from db import connection_db
from db.document_store import DocumentStore

TEST_DB = "f1ndr_test"


@pytest.fixture
def settings_env(monkeypatch):
    """Isolate settings from the developer's .env and reset cached settings."""
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret")
    monkeypatch.setenv("MONGODB_DB_NAME", TEST_DB)
    monkeypatch.setenv("MONGODB_TIMEOUT_MS", "300")
    get_settings.cache_clear()
    yield monkeypatch
    get_settings.cache_clear()


def _explicit_mongo_uri():
    """Only use Mongo when MONGODB_URI is set in the process env (e.g. CI), never from .env."""
    uri = os.environ.get("MONGODB_URI")
    if not uri:
        return None
    try:
        MongoClient(uri, serverSelectionTimeoutMS=500)[TEST_DB].list_collection_names()
        return uri
    except PyMongoError:
        return None


async def _exercise_store(store: DocumentStore):
    assert await store.upsert({"id": "a", "n": 1, "tag": "x"}) is False
    assert await store.upsert({"id": "b", "n": 2, "tag": "x"}) is False
    assert await store.upsert({"id": "a", "n": 3, "tag": "y"}) is True
    assert (await store.get("a"))["n"] == 3
    assert "_id" not in await store.get("a")
    assert await store.get("missing") is None
    assert await store.count({"tag": "x"}) == 1
    assert [d["id"] for d in await store.find(sort=("n", -1))] == ["a", "b"]
    assert len(await store.find(skip=1, limit=1)) == 1
    assert await store.delete("a") is True
    assert await store.delete("a") is False
    assert await store.count() == 1


async def test_document_store_in_memory():
    await _exercise_store(DocumentStore(f"mem_{uuid.uuid4().hex}"))


async def test_startup_falls_back_to_memory_when_mongo_unreachable(settings_env):
    from api.shutdown import on_shutdown
    from api.startup import on_startup
    from fastapi import FastAPI

    settings_env.setenv("MONGODB_URI", "mongodb://127.0.0.1:1")
    settings_env.setenv("ENVIRONMENT", "development")
    settings_env.setenv("MONGODB_REQUIRED", "false")
    app = FastAPI()
    await on_startup(app)
    assert connection_db.get_database() is None
    await on_shutdown(app)


async def test_startup_fails_when_mongo_required(settings_env):
    from api.startup import on_startup
    from fastapi import FastAPI

    settings_env.setenv("MONGODB_URI", "mongodb://127.0.0.1:1")
    settings_env.setenv("MONGODB_REQUIRED", "true")
    with pytest.raises(RuntimeError, match="MongoDB is required"):
        await on_startup(FastAPI())


def test_production_requires_mongo_by_default(settings_env):
    settings_env.setenv("ENVIRONMENT", "production")
    settings_env.delenv("MONGODB_REQUIRED", raising=False)
    assert get_settings().mongodb_required is True


async def test_document_store_and_modules_on_mongo(settings_env):
    uri = _explicit_mongo_uri()
    if uri is None:
        pytest.skip("Set MONGODB_URI in the environment to an authorized MongoDB to run")
    from api.shutdown import on_shutdown
    from api.startup import on_startup
    from fastapi import FastAPI
    from listr.core.core import push_listing
    from listr.db.listing_repo import listings_store
    from trinn.db.trinn_repo import get_task_repo

    settings_env.setenv("MONGODB_URI", uri)
    app = FastAPI()
    await on_startup(app)
    database = connection_db.get_database()
    try:
        assert database is not None and database.name == TEST_DB
        get_task_repo()

        store = DocumentStore(f"test_store_{uuid.uuid4().hex}")
        await _exercise_store(store)
        await database.drop_collection(store.collection_name)

        pushed = await push_listing("kijiji", {"title": "Mongo listing"})
        stored = await listings_store.get(f"kijiji:{pushed['listing']['id']}")
        assert stored["title"] == "Mongo listing"
        await listings_store.delete(stored["key"])
    finally:
        await on_shutdown(app)
    assert connection_db.get_database() is None
