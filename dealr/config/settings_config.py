"""dealr — application settings via Pydantic BaseSettings."""

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── App ──────────────────────────────────────────────────────────────────
    app_name: str = Field(default="dealr")
    app_version: str = Field(default="0.1.0")
    debug: bool = Field(default=False)
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000", "https://dealr.app"]
    )

    # ── MongoDB ───────────────────────────────────────────────────────────────
    mongodb_uri: str = Field(default="mongodb://localhost:27017")
    mongodb_db_name: str = Field(default="dealr")

    # ── JWT ───────────────────────────────────────────────────────────────────
    jwt_secret_key: str = Field(...)
    jwt_algorithm: str = Field(default="HS256")
    jwt_access_token_expire_minutes: int = Field(default=1440)

    # ── NHTSA vPIC ────────────────────────────────────────────────────────────
    nhtsa_base_url: str = Field(
        default="https://vpic.nhtsa.dot.gov/api/vehicles"
    )
    vin_cache_ttl_seconds: int = Field(default=0)

    # ── HTTP Client ───────────────────────────────────────────────────────────
    http_timeout_seconds: float = Field(default=10.0)
    http_max_connections: int = Field(default=100)
    http_max_keepalive_connections: int = Field(default=20)

    # ── Bulk VIN Jobs ─────────────────────────────────────────────────────────
    bulk_vin_batch_size: int = Field(default=50)
    bulk_vin_worker_concurrency: int = Field(default=5)

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings singleton."""
    return Settings()  # type: ignore[call-arg]
