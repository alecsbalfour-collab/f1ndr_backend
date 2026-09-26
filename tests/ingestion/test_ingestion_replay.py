# f1ndr_backend/tests/ingestion/test_ingestion_replay.py
import os

import pytest
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from pipelines.ingestion_history import record_ingestion

TEST_DB = "f1ndr_test"
MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")


def _mongo_available() -> bool:
    try:
        MongoClient(MONGO_URI, serverSelectionTimeoutMS=500)[TEST_DB].list_collection_names()
        return True
    except PyMongoError:
        return False


@pytest.mark.skipif(not _mongo_available(), reason="MongoDB not reachable or not authorized (set MONGODB_URI)")
@pytest.mark.asyncio
async def test_ingestion_replay_record():
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[TEST_DB]

    await db.ingestion_history.delete_many({"source": "test_source"})
    await record_ingestion(db, source="test_source", count=5)

    doc = await db.ingestion_history.find_one({"source": "test_source"})
    assert doc is not None
    assert doc["count"] == 5
