# db/migrations.py
"""
Versioned schema/index migrations, applied at startup before the declarative indexes.

DocumentStore declarations and dealr's `_ensure_indexes` describe indexes that should
exist and are re-applied on every start. Migrations cover what `create_index` can't:
dropping or renaming indexes, changing index options (unique, TTL), and data backfills.

Rules for adding one:
- Append a `Migration` with the next version; never edit, renumber or remove applied ones.
- `up` must be idempotent: a crash between running it and recording it re-runs it.

CLI:  python -m db.migrations status | up
"""

import asyncio
import logging
import os
import socket
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Awaitable, Callable, Dict, List, Sequence

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError

logger = logging.getLogger(__name__)

COLLECTION = "schema_migrations"
LOCK_ID = "lock"
LOCK_TTL = timedelta(minutes=10)


@dataclass(frozen=True)
class Migration:
    version: int
    name: str
    up: Callable[[AsyncIOMotorDatabase], Awaitable[None]]


async def _baseline(db: AsyncIOMotorDatabase) -> None:
    """Start version tracking; the current indexes come from the declarative definitions."""


async def _vehicle_category_default(db: AsyncIOMotorDatabase) -> None:
    """Backfill `category: "car"` on listing documents written before the field existed."""
    # `{field: None}` matches both missing and explicit-null values.
    for name in ("dealr_inventory", "sellr_listings", "listr_listings"):
        await db[name].update_many({"category": None}, {"$set": {"category": "car"}})


async def _category_verticals(db: AsyncIOMotorDatabase) -> None:
    """Split `category` into a classifieds vertical + a vehicle subcategory.

    Listings predate non-vehicle support, so every document holding a vehicle-kind
    category (or none) moves to `category: "vehicles"` and keeps the old value as
    `subcategory` (`"car"` when it was missing).
    """
    vehicle_kinds = [
        "car", "truck", "motorcycle", "motorhome_a", "motorhome_b", "motorhome_c",
        "travel_trailer", "fifth_wheel", "toy_hauler", "truck_camper", "other",
        None,  # missing or explicit-null
    ]
    for name in ("dealr_inventory", "sellr_listings", "listr_listings", "listings", "f1ndr_listings"):
        await db[name].update_many(
            {"category": {"$in": vehicle_kinds}},
            [{"$set": {"subcategory": {"$ifNull": ["$category", "car"]}, "category": "vehicles"}}],
        )


MIGRATIONS: List[Migration] = [
    Migration(1, "baseline", _baseline),
    Migration(2, "vehicle_category_default", _vehicle_category_default),
    Migration(3, "category_verticals", _category_verticals),
]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _validate(migrations: Sequence[Migration]) -> List[Migration]:
    versions = [m.version for m in migrations]
    if len(set(versions)) != len(versions) or any(v < 1 for v in versions):
        raise ValueError(f"Migration versions must be unique positive integers: {versions}")
    return sorted(migrations, key=lambda m: m.version)


async def _acquire_lock(col, owner: str) -> bool:
    """Take the lock if it's free or expired; a live lock makes the upsert hit a duplicate _id."""
    now = _now()
    try:
        await col.find_one_and_update(
            {"_id": LOCK_ID, "expires_at": {"$lt": now}},
            {"$set": {"owner": owner, "expires_at": now + LOCK_TTL}},
            upsert=True,
        )
        return True
    except DuplicateKeyError:
        return False


async def applied_versions(db: AsyncIOMotorDatabase) -> Dict[int, dict]:
    cursor = db[COLLECTION].find({"version": {"$exists": True}})
    return {doc["version"]: doc async for doc in cursor}


async def migration_status(db: AsyncIOMotorDatabase, migrations: Sequence[Migration] = MIGRATIONS) -> dict:
    ordered = _validate(migrations)
    applied = await applied_versions(db)
    return {
        "current": max(applied, default=0),
        "latest": ordered[-1].version if ordered else 0,
        "pending": [f"{m.version:04d}_{m.name}" for m in ordered if m.version not in applied],
        "unknown": sorted(set(applied) - {m.version for m in ordered}),
    }


async def apply_migrations(
    db: AsyncIOMotorDatabase,
    migrations: Sequence[Migration] = MIGRATIONS,
    lock_wait_seconds: float = 120.0,
    poll_seconds: float = 0.5,
) -> List[int]:
    """Apply pending migrations under a cross-process lock; returns the versions applied."""
    ordered = _validate(migrations)
    col = db[COLLECTION]
    owner = f"{socket.gethostname()}:{os.getpid()}:{uuid.uuid4().hex[:8]}"
    loop = asyncio.get_running_loop()
    deadline = loop.time() + lock_wait_seconds
    while not await _acquire_lock(col, owner):
        if loop.time() > deadline:
            raise RuntimeError("Timed out waiting for the schema migration lock")
        await asyncio.sleep(poll_seconds)

    try:
        applied = await applied_versions(db)
        unknown = set(applied) - {m.version for m in ordered}
        if unknown:
            logger.warning("Database has migrations this build doesn't know: %s", sorted(unknown))
        ran = []
        for migration in ordered:
            if migration.version in applied:
                continue
            await col.update_one({"_id": LOCK_ID, "owner": owner}, {"$set": {"expires_at": _now() + LOCK_TTL}})
            logger.info("Applying migration %04d_%s", migration.version, migration.name)
            await migration.up(db)
            await col.insert_one(
                {"_id": migration.version, "version": migration.version, "name": migration.name, "applied_at": _now()}
            )
            ran.append(migration.version)
        return ran
    finally:
        await col.delete_one({"_id": LOCK_ID, "owner": owner})


async def _cli(command: str) -> int:
    from motor.motor_asyncio import AsyncIOMotorClient

    from api.config.settings_config import get_settings

    settings = get_settings()
    client = AsyncIOMotorClient(settings.MONGODB_URI, serverSelectionTimeoutMS=settings.MONGODB_TIMEOUT_MS)
    try:
        db = client[settings.MONGODB_DB_NAME]
        if command == "up":
            print(f"Applied: {await apply_migrations(db) or 'nothing pending'}")
        print(await migration_status(db))
        return 0
    finally:
        client.close()


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd not in ("status", "up"):
        sys.exit("usage: python -m db.migrations [status|up]")
    logging.basicConfig(level=logging.INFO)
    sys.exit(asyncio.run(_cli(cmd)))
