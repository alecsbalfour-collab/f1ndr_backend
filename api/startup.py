# f1ndr_backend/api/startup.py

import logging

from fastapi import FastAPI

from api.config.settings_config import get_settings
from db.connection_db import connect_to_db, get_client, get_database
from db.document_store import ensure_all_indexes
from db.migrations import apply_migrations

logger = logging.getLogger(__name__)


async def on_startup(app: FastAPI) -> None:
    """Open the shared Mongo connection, hand it to every module, and start the scheduler."""
    if await connect_to_db(app):
        from dealr.db.client_db import attach_database
        from trinn.db.trinn_repo import initialize_task_repo

        database = get_database()
        await apply_migrations(database)
        initialize_task_repo(database)
        await attach_database(get_client(), database)
        await ensure_all_indexes()
        logger.info("Module storage initialized on MongoDB")

    await _start_scheduler()


async def _start_scheduler() -> None:
    """In-process scheduler stopgap until the ARQ worker lands.

    Only safe with a single worker: each process owns its own in-memory task
    table, so WORKERS>1 would both lose tasks and double-run them.
    """
    from trinn.utils.scheduler import get_scheduler

    if get_settings().WORKERS > 1:
        logger.warning(
            "WORKERS>1: trinn scheduler left stopped; in-process scheduling "
            "would double-run tasks. Use the ARQ worker (roadmap) instead."
        )
        return
    await get_scheduler().start()
    logger.info("Trinn scheduler started in-process (WORKERS=1 stopgap)")
