# f1ndr_backend/api/app_lifecycles.py

from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.startup import on_startup
from api.shutdown import on_shutdown


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan: runs startup before serving and shutdown after."""
    await on_startup(app)
    try:
        yield
    finally:
        await on_shutdown(app)
