from fastapi import FastAPI
from api.app_lifecycles import lifespan
from api.config.cors_config import apply_cors
from api.router_api import api_router

app = FastAPI(
    title="f1ndr Backend",
    version="1.0.0",
    lifespan=lifespan,
)

apply_cors(app)

# Mount the global router
app.include_router(api_router)
