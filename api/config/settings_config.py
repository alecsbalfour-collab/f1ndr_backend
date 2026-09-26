from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    # Database
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "f1ndr"
    MONGODB_TIMEOUT_MS: int = 3000
    # None = required only when ENVIRONMENT is "production"
    MONGODB_REQUIRED: Optional[bool] = None

    # JWT / Security
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"

    # App Environment
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "info"

    # App Metadata
    APP_NAME: str = "f1ndr API"
    VERSION: str = "1.0.0"
    DEBUG: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def mongodb_required(self) -> bool:
        if self.MONGODB_REQUIRED is not None:
            return self.MONGODB_REQUIRED
        return self.ENVIRONMENT == "production"

@lru_cache
def get_settings() -> Settings:
    return Settings()
