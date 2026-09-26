# f1ndr_backend/api/shutdown.py

from fastapi import FastAPI

from db.connection_db import close_db_connection


async def on_shutdown(app: FastAPI) -> None:
    """Detach module storage and close the shared Mongo connection."""
    from dealr.db.client_db import close_db
    from trinn.db.trinn_repo import reset_task_repo

    reset_task_repo()
    await close_db()
    await close_db_connection(app)
