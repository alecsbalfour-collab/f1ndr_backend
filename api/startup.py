# f1ndr_backend/api/startup.py

import logging

from fastapi import FastAPI

from db.connection_db import connect_to_db, get_client, get_database
from db.document_store import ensure_all_indexes
from db.migrations import apply_migrations

logger = logging.getLogger(__name__)


async def on_startup(app: FastAPI) -> None:
    """Open the shared Mongo connection and hand it to every module that persists data."""
    if not await connect_to_db(app):
        return

    from dealr.db.client_db import attach_database
    from trinn.db.trinn_repo import initialize_task_repo

    database = get_database()
    await apply_migrations(database)
    initialize_task_repo(database)
    await attach_database(get_client(), database)
    await ensure_all_indexes()
    logger.info("Module storage initialized on MongoDB")
