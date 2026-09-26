# db/connection_db.py
# Shared MongoDB connection for the whole backend. Opened once at app startup.

import logging
from typing import Optional

from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import PyMongoError

from api.config.settings_config import get_settings

logger = logging.getLogger(__name__)

client: Optional[AsyncIOMotorClient] = None
db: Optional[AsyncIOMotorDatabase] = None


def get_client() -> Optional[AsyncIOMotorClient]:
    return client


def get_database() -> Optional[AsyncIOMotorDatabase]:
    """Shared database, or None when running on the in-memory fallback."""
    return db


async def connect_to_db(app: Optional[FastAPI] = None) -> bool:
    """
    Connect to MongoDB. Returns True when connected. When Mongo is unavailable,
    raises if settings.mongodb_required, otherwise logs and returns False.
    """
    global client, db
    settings = get_settings()
    candidate = AsyncIOMotorClient(settings.MONGODB_URI, serverSelectionTimeoutMS=settings.MONGODB_TIMEOUT_MS)
    database = candidate[settings.MONGODB_DB_NAME]
    try:
        # list_collection_names needs auth, unlike ping, so it verifies credentials too
        await database.list_collection_names()
    except PyMongoError as exc:
        candidate.close()
        if settings.mongodb_required:
            raise RuntimeError(f"MongoDB is required but unavailable: {exc}") from exc
        logger.warning("MongoDB unavailable (%s); using in-memory storage", type(exc).__name__)
        return False

    client, db = candidate, database
    if app is not None:
        app.state.db = db
    logger.info("Connected to MongoDB database: %s", settings.MONGODB_DB_NAME)
    return True


async def close_db_connection(app: Optional[FastAPI] = None) -> None:
    global client, db
    if client is not None:
        client.close()
        logger.info("MongoDB connection closed")
    client, db = None, None
    if app is not None:
        app.state.db = None
