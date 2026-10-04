"""dealr.db.collections_db — Typed collection accessors."""

from motor.motor_asyncio import AsyncIOMotorCollection

from dealr.db.client_db import get_database


def get_dealers_collection() -> AsyncIOMotorCollection:
    return get_database()["dealers"]


def get_bulk_jobs_collection() -> AsyncIOMotorCollection:
    return get_database()["bulk_vin_jobs"]


def get_vin_cache_collection() -> AsyncIOMotorCollection:
    return get_database()["vin_cache"]
