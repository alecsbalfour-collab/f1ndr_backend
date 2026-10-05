# f1ndr_backend/api/shutdown.py

from fastapi import FastAPI

from db.connection_db import close_db_connection


async def on_shutdown(app: FastAPI) -> None:
    """Stop the scheduler, detach module storage and close the shared Mongo connection."""
    from dealr.db.client_db import close_db
    from trinn.utils.scheduler import stop_scheduler

    await stop_scheduler()
    await close_db()
    await close_db_connection(app)
