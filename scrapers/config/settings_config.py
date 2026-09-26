# scrapers/config/settings_config.py

import os
from dataclasses import dataclass, fields

ENV_PREFIX = "f1ndr_SCRAPER_"

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


@dataclass(frozen=True)
class ScraperConfig:
    """
    Runtime settings shared by every scraper.
    Each field can be overridden with an env var, e.g. f1ndr_SCRAPER_MAX_RETRIES=5.
    """
    headless: bool = True
    timeout_ms: int = 30000
    selector_timeout_ms: int = 15000
    wait_until: str = "domcontentloaded"
    user_agent: str = DEFAULT_USER_AGENT
    viewport_width: int = 1920
    viewport_height: int = 1080
    locale: str = "en-CA"
    max_retries: int = 2
    retry_delay: float = 1.0
    cache_ttl_seconds: int = 300
    breaker_failure_threshold: int = 3
    breaker_reset_seconds: float = 300.0
    max_concurrency: int = 3

    @classmethod
    def from_env(cls) -> "ScraperConfig":
        overrides = {}
        for field in fields(cls):
            raw = os.getenv(f"{ENV_PREFIX}{field.name.upper()}")
            if raw is None:
                continue
            if isinstance(field.default, bool):
                overrides[field.name] = raw.strip().lower() in ("1", "true", "yes")
            else:
                overrides[field.name] = type(field.default)(raw)
        return cls(**overrides)


def load_scraper_settings() -> dict:
    return {
        "SCRAPER_ENV": os.getenv("f1ndr_SCRAPER_ENV", "dev"),
        "SCRAPER_DEBUG": os.getenv("f1ndr_SCRAPER_DEBUG", "false").lower() == "true",
        "VERSION": "1.0.0",
    }

def validate_scraper_settings(cfg: dict) -> bool:
    return (
        isinstance(cfg, dict)
        and "SCRAPER_ENV" in cfg
        and "SCRAPER_DEBUG" in cfg
    )
