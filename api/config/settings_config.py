from typing import Optional

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

MIN_PRODUCTION_SECRET_LENGTH = 32
PLACEHOLDER_SECRETS = {"changeme", "change-me", "secret", "jwt-secret", "test-secret", "dev", "development"}


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
    # Comma-separated; these accounts get the admin role once their email is verified
    ADMIN_EMAILS: str = ""

    # Outbound email (verification links). No SMTP_HOST = log links in dev, skip in production.
    EMAIL_FROM: str = "f1ndr <notifications@f1ndr.ca>"
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_STARTTLS: bool = True
    SMTP_SSL: bool = False
    SMTP_TIMEOUT_SECONDS: int = 10
    # Frontend page that receives ?token=...; defaults to this API's GET /auth/verify-email
    EMAIL_VERIFICATION_URL: Optional[str] = None
    # Frontend page that receives ?token=... for password reset; must point at the app's reset form
    PASSWORD_RESET_URL: Optional[str] = None

    # App Environment
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "info"

    # App Metadata
    APP_NAME: str = "f1ndr API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Server (read by run_backend.py)
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    WORKERS: int = 1
    RELOAD: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def _reject_weak_production_secret(self) -> "Settings":
        if self.ENVIRONMENT == "production":
            secret = self.JWT_SECRET_KEY.strip()
            if len(secret) < MIN_PRODUCTION_SECRET_LENGTH or secret.lower() in PLACEHOLDER_SECRETS:
                raise ValueError(
                    f"JWT_SECRET_KEY must be at least {MIN_PRODUCTION_SECRET_LENGTH} characters "
                    "and not a placeholder when ENVIRONMENT=production"
                )
        return self

    @property
    def mongodb_required(self) -> bool:
        if self.MONGODB_REQUIRED is not None:
            return self.MONGODB_REQUIRED
        return self.ENVIRONMENT == "production"

    @property
    def admin_emails(self) -> set:
        return {e.strip().lower() for e in self.ADMIN_EMAILS.split(",") if e.strip()}

@lru_cache
def get_settings() -> Settings:
    return Settings()
