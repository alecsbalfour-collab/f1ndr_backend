from fastapi import FastAPI
from fastapi.routing import APIRoute
from slowapi.middleware import SlowAPIMiddleware
from api.app_lifecycles import lifespan
from api.config.cors_config import apply_cors
from api.errors.exception_handlers import register_exception_handlers
from api.middleware import (
    DeprecationMiddleware,
    ErrorHandlerMiddleware,
    RequestIDMiddleware,
    RequestTimerMiddleware,
    SecureHeadersMiddleware,
)
from api.router_api import API_V1_PREFIX, LEGACY_PREFIXES, api_router, health_router
from api.schemas.common import error_responses
from api.security.rate_limiter import limiter


def _operation_id(route: APIRoute) -> str:
    """Stable `<tag>_<function>` operation IDs, used as method names by generated clients."""
    return f"{route.tags[0]}_{route.name}" if route.tags else route.name


app = FastAPI(
    title="f1ndr Backend",
    version="1.0.0",
    lifespan=lifespan,
    generate_unique_id_function=_operation_id,
)

app.state.limiter = limiter
register_exception_handlers(app)

# Last added runs first: CORS -> request ID -> secure headers -> deprecation -> timer -> rate limit -> error handler
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(RequestTimerMiddleware)
app.add_middleware(DeprecationMiddleware, prefixes=LEGACY_PREFIXES, successor_prefix=API_V1_PREFIX)
app.add_middleware(SecureHeadersMiddleware)
app.add_middleware(RequestIDMiddleware)
apply_cors(app)

# Infrastructure probes stay unversioned.
app.include_router(health_router)
# Versioned API. Mounted first so url_for() resolves route names to the /api/v1 paths.
app.include_router(api_router, prefix=API_V1_PREFIX, responses=error_responses(422, 429, 500))
# Deprecated unversioned aliases for clients built before /api/v1; hidden from the OpenAPI spec.
# Remove this line once no traffic hits them (DeprecationMiddleware logs each path used).
app.include_router(api_router, include_in_schema=False)
