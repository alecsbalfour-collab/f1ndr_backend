from .dealr_routes import router as dealr_router
from .listr_routes import router as listr_router
from .f1ndr_routes import router as f1ndr_router
from .sellr_routes import router as sellr_router
from .trinn_routes import router as trinn_router
from .watchr_routes import router as watchr_router

__all__ = [
    "dealr_router",
    "listr_router",
    "f1ndr_router",
    "sellr_router",
    "trinn_router",
    "watchr_router",
]
