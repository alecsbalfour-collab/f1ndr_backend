from fastapi import APIRouter

# Correct imports — routers live in api/routes/
from api.routes.dealr_routes import router as dealr_router
from api.routes.sellr_routes import router as sellr_router
from api.routes.listr_routes import router as listr_router
from api.routes.trinn_routes import router as trinn_router
from api.routes.watchr_routes import router as watchr_router
from api.routes.f1ndr_routes import router as f1ndr_router

api_router = APIRouter()

# Mount module routers with prefixes
api_router.include_router(dealr_router, prefix="/dealr")
api_router.include_router(sellr_router, prefix="/sellr")
api_router.include_router(listr_router, prefix="/listr")
api_router.include_router(trinn_router, prefix="/trinn")
api_router.include_router(watchr_router, prefix="/watchr")
api_router.include_router(f1ndr_router, prefix="/f1ndr")
