# f1ndr-backend/api/router_api.py
"""
DICT-aligned API router with FlutterFlow compatibility and enterprise features.
"""

import logging
from fastapi import APIRouter

# Correct imports — routers live in api/routes/
from api.routes.dealr_routes import router as dealr_router
from api.routes.sellr_routes import router as sellr_router
from api.routes.listr_routes import router as listr_router
from api.routes.trinn_routes import router as trinn_router
from api.routes.watchr_routes import router as watchr_router
from api.routes.f1ndr_routes import router as f1ndr_router
from api.routes.auth_routes import router as auth_router
from api.routes.scraper_routes import router as scraper_router
from api.routes.controllers.health_controller import router as health_router
from api.routes.controllers.version_controller import router as version_router
from api.routes.controllers.list_controller import router as list_controller_router


logger = logging.getLogger(__name__)

api_router = APIRouter()

# Mount module routers with prefixes
api_router.include_router(dealr_router, prefix="/dealr")
api_router.include_router(sellr_router, prefix="/sellr")
api_router.include_router(listr_router, prefix="/listr")
api_router.include_router(trinn_router, prefix="/trinn")
api_router.include_router(watchr_router, prefix="/watchr")
api_router.include_router(f1ndr_router, prefix="/f1ndr")
api_router.include_router(auth_router, prefix="/auth")
api_router.include_router(scraper_router, prefix="/scrapers")

# Mount controller routers
api_router.include_router(health_router)
api_router.include_router(version_router)
api_router.include_router(list_controller_router)

logger.info("API routes configured with FlutterFlow compatibility")
