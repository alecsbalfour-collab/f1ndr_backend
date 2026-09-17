"""dealr.db.client_db — Motor async MongoDB client singleton."""

import logging
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from dealr.config import get_settings

logger = logging.getLogger(__name__)

_client:   Optional[AsyncIOMotorClient]   = None
_database: Optional[AsyncIOMotorDatabase] = None


async def init_db() -> None:
    global _client, _database
    settings = get_settings()
    _client   = AsyncIOMotorClient(settings.mongodb_uri)
    _database = _client[settings.mongodb_db_name]
    await _ensure_indexes(_database)
    logger.info("MongoDB connected — database: %s", settings.mongodb_db_name)


async def close_db() -> None:
    global _client, _database
    if _client is not None:
        _client.close()
        _client   = None
        _database = None
        logger.info("MongoDB connection closed.")


def get_client() -> AsyncIOMotorClient:
    if _client is None:
        raise RuntimeError("Database not initialised. Call init_db() first.")
    return _client


def get_database() -> AsyncIOMotorDatabase:
    if _database is None:
        raise RuntimeError("Database not initialised. Call init_db() first.")
    return _database


async def _ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    from pymongo import ASCENDING, DESCENDING

    # ── dealers ───────────────────────────────────────────────────────────────
    await db["dealers"].create_index(
        [("email", ASCENDING)], unique=True, name="dealers_email_unique"
    )
    await db["dealers"].create_index(
        [("dealer_id", ASCENDING)], unique=True, name="dealers_dealer_id_unique"
    )

    # ── listings ──────────────────────────────────────────────────────────────
    await db["listings"].create_index(
        [("listing_id", ASCENDING)], unique=True, name="listings_listing_id_unique"
    )
    await db["listings"].create_index(
        [("dealer_id", ASCENDING), ("created_at", DESCENDING)],
        name="listings_dealer_created",
    )
    await db["listings"].create_index(
        [("vin", ASCENDING)], name="listings_vin"
    )
    await db["listings"].create_index(
        [("listing_status", ASCENDING)], name="listings_status"
    )

    # ── bulk_vin_jobs ─────────────────────────────────────────────────────────
    await db["bulk_vin_jobs"].create_index(
        [("job_id", ASCENDING)], unique=True, name="bulk_jobs_job_id_unique"
    )
    await db["bulk_vin_jobs"].create_index(
        [("dealer_id", ASCENDING)], name="bulk_jobs_dealer_id"
    )

    # ── vin_cache ─────────────────────────────────────────────────────────────
    await db["vin_cache"].create_index(
        [("vin", ASCENDING)], unique=True, name="vin_cache_vin_unique"
    )

    logger.info("MongoDB indexes ensured.")
