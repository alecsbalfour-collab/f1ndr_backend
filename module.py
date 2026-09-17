from fastapi import FastAPI
from api.router_api import api_router

def create_app():
    app = FastAPI()
    app.include_router(api_router)
    return app

app = create_app()
