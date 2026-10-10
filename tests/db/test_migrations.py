"""Versioned migrations: ordering, idempotent re-runs, cross-process lock, startup wiring."""

import asyncio
import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from db.migrations import COLLECTION, LOCK_ID, MIGRATIONS, Migration, apply_migrations, migration_status


def test_versions_must_be_unique():
    async def noop(db):
        pass

    with pytest.raises(ValueError, match="unique"):
        asyncio.run(apply_migrations(None, [Migration(1, "a", noop), Migration(1, "b", noop)]))


def test_registry_is_valid():
    versions = [m.version for m in MIGRATIONS]
    assert versions == sorted(set(versions)) and versions[0] == 1


@pytest.fixture
def mongo_db():
    """Throwaway Motor database; sync fixture because Motor binds to the test's event loop lazily."""
    uri = os.environ.get("MONGODB_URI")
    if not uri:
        pytest.skip("Set MONGODB_URI in the environment to run Mongo migration tests")
    name = f"f1ndr_test_migr_{uuid.uuid4().hex[:8]}"
    sync_client = MongoClient(uri, serverSelectionTimeoutMS=1000)
    try:
        sync_client.admin.command("ping")
    except PyMongoError:
        pytest.skip("MongoDB at MONGODB_URI is not reachable")
    client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=1000)
    yield client[name]
    client.close()
    sync_client.drop_database(name)
    sync_client.close()


def _recording_migrations(calls):
    def make(version, name):
        async def up(db):
            calls.append(version)
            await db.things.create_index("v2" if version == 2 else "v1", name=f"things_{name}")
        return Migration(version, name, up)

    return [make(2, "second"), make(1, "first")]


async def test_applies_in_order_once(mongo_db):
    calls = []
    migrations = _recording_migrations(calls)
    assert await apply_migrations(mongo_db, migrations) == [1, 2]
    assert await apply_migrations(mongo_db, migrations) == []
    assert calls == [1, 2]
    status = await migration_status(mongo_db, migrations)
    assert status == {"current": 2, "latest": 2, "pending": [], "unknown": []}
    assert await mongo_db[COLLECTION].find_one({"_id": LOCK_ID}) is None


async def test_failed_migration_is_retried_and_releases_lock(mongo_db):
    attempts = []

    async def flaky(db):
        attempts.append(1)
        if len(attempts) == 1:
            raise RuntimeError("boom")

    migrations = [Migration(1, "flaky", flaky)]
    with pytest.raises(RuntimeError, match="boom"):
        await apply_migrations(mongo_db, migrations)
    assert await mongo_db[COLLECTION].find_one({"_id": LOCK_ID}) is None
    assert (await migration_status(mongo_db, migrations))["pending"] == ["0001_flaky"]
    assert await apply_migrations(mongo_db, migrations) == [1]


async def test_concurrent_runners_apply_each_migration_once(mongo_db):
    calls = []

    async def slow(db):
        calls.append(1)
        await asyncio.sleep(0.2)

    migrations = [Migration(1, "slow", slow)]
    results = await asyncio.gather(*(apply_migrations(mongo_db, migrations, poll_seconds=0.05) for _ in range(3)))
    assert calls == [1]
    assert sorted(results) == [[], [], [1]]


async def test_live_lock_times_out_and_expired_lock_is_taken_over(mongo_db):
    col = mongo_db[COLLECTION]
    future = datetime.now(timezone.utc) + timedelta(minutes=5)
    await col.insert_one({"_id": LOCK_ID, "owner": "someone-else", "expires_at": future})
    with pytest.raises(RuntimeError, match="lock"):
        await apply_migrations(mongo_db, MIGRATIONS, lock_wait_seconds=0.2, poll_seconds=0.05)

    await col.update_one({"_id": LOCK_ID}, {"$set": {"expires_at": datetime.now(timezone.utc) - timedelta(seconds=1)}})
    assert await apply_migrations(mongo_db, MIGRATIONS) == [m.version for m in MIGRATIONS]


async def test_startup_applies_migrations(mongo_db, monkeypatch):
    from fastapi import FastAPI

    from api.config.settings_config import get_settings
    from api.shutdown import on_shutdown
    from api.startup import on_startup

    monkeypatch.setenv("MONGODB_URI", os.environ["MONGODB_URI"])
    monkeypatch.setenv("MONGODB_DB_NAME", mongo_db.name)
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret")
    get_settings.cache_clear()
    app = FastAPI()
    try:
        await on_startup(app)
        assert (await migration_status(app.state.db))["pending"] == []
    finally:
        await on_shutdown(app)
        get_settings.cache_clear()


async def test_category_split_backfills_vehicles(mongo_db):
    for name in ("dealr_inventory", "sellr_listings", "listr_listings"):
        await mongo_db[name].insert_many([
            {"id": "missing"},
            {"id": "null", "category": None},
            {"id": "truck", "category": "truck"},
            {"id": "goods", "category": "goods"},
        ])
    await apply_migrations(mongo_db)
    for name in ("dealr_inventory", "sellr_listings", "listr_listings"):
        docs = {d["id"]: d async for d in mongo_db[name].find()}
        assert (docs["missing"]["category"], docs["missing"]["subcategory"]) == ("vehicles", "car")
        assert (docs["null"]["category"], docs["null"]["subcategory"]) == ("vehicles", "car")
        assert (docs["truck"]["category"], docs["truck"]["subcategory"]) == ("vehicles", "truck")
        assert docs["goods"]["category"] == "goods" and "subcategory" not in docs["goods"]


async def test_unrunnable_sync_tasks_dropped(mongo_db):
    listing = {"title": "Bike", "price": 100}
    await mongo_db["trinn_tasks"].insert_many([
        # Legacy sellr shape: no platform, listing never had an id.
        {"task_id": "legacy-sellr", "task": "sync", "task_data": {"task": "sync", "platform": None, "listing": listing}},
        # Legacy dealr update: id present, platform missing.
        {"task_id": "legacy-dealr", "task": "sync", "task_data": {"task": "sync", "listing": {**listing, "id": "inv1"}}},
        # Legacy but runnable: platform + id. Kept.
        {"task_id": "legacy-ok", "task": "sync",
         "task_data": {"task": "sync", "platform": "kijiji", "listing": {**listing, "id": "inv2"}}},
        # Current shape. Kept.
        {"task_id": "sync:kijiji:l1", "task": "sync", "listing_id": "l1",
         "task_data": {"task": "sync", "platform": "kijiji", "listing": {**listing, "id": "l1"}}},
        # Other task types. Kept.
        {"task_id": "vin-1", "task": "vin", "task_data": {"task": "vin", "vin": "1HGCM82633A004352"}},
    ])
    await apply_migrations(mongo_db)
    remaining = {d["task_id"] async for d in mongo_db["trinn_tasks"].find()}
    assert remaining == {"legacy-ok", "sync:kijiji:l1", "vin-1"}


async def test_unknown_applied_versions_are_reported(mongo_db):
    await mongo_db[COLLECTION].insert_one({"_id": 999, "version": 999, "name": "from_the_future"})
    status = await migration_status(mongo_db)
    assert status["unknown"] == [999] and status["current"] == 999
