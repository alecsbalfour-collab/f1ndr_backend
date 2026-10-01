"""Server/deployment settings: defaults, production secret check, run_backend wiring."""

import pytest
from pydantic import ValidationError

import run_backend
from api.config.settings_config import Settings, get_settings

STRONG_SECRET = "x" * 48


@pytest.fixture
def env(monkeypatch):
    """Isolate from the developer's .env and reset cached settings."""
    for key in ("ENVIRONMENT", "DEBUG", "HOST", "PORT", "WORKERS", "RELOAD", "LOG_LEVEL"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("JWT_SECRET_KEY", "dev-secret")
    get_settings.cache_clear()
    yield monkeypatch
    get_settings.cache_clear()


def _settings():
    return Settings(_env_file=None)


def test_safe_defaults(env):
    settings = _settings()
    assert settings.DEBUG is False
    assert settings.RELOAD is False
    assert (settings.HOST, settings.PORT, settings.WORKERS) == ("127.0.0.1", 8000, 1)


@pytest.mark.parametrize("secret", ["changeme", "short-secret", " " * 40, "CHANGEME"])
def test_production_rejects_weak_secret(env, secret):
    env.setenv("ENVIRONMENT", "production")
    env.setenv("JWT_SECRET_KEY", secret)
    with pytest.raises(ValidationError, match="JWT_SECRET_KEY"):
        _settings()


def test_production_accepts_strong_secret(env):
    env.setenv("ENVIRONMENT", "production")
    env.setenv("JWT_SECRET_KEY", STRONG_SECRET)
    assert _settings().JWT_SECRET_KEY == STRONG_SECRET


def test_weak_secret_allowed_outside_production(env):
    env.setenv("ENVIRONMENT", "development")
    env.setenv("JWT_SECRET_KEY", "changeme")
    assert _settings().ENVIRONMENT == "development"


async def test_production_startup_fails_on_weak_secret(env):
    from fastapi import FastAPI

    from api.startup import on_startup

    env.setenv("ENVIRONMENT", "production")
    env.setenv("JWT_SECRET_KEY", "changeme")
    with pytest.raises(ValidationError, match="JWT_SECRET_KEY"):
        await on_startup(FastAPI())


def _captured_run(monkeypatch):
    calls = []
    monkeypatch.setattr(run_backend.uvicorn, "run", lambda app, **kwargs: calls.append((app, kwargs)))
    run_backend.main()
    return calls[0]


def test_run_backend_uses_settings(env):
    env.setenv("HOST", "0.0.0.0")
    env.setenv("PORT", "9001")
    env.setenv("WORKERS", "4")
    env.setenv("LOG_LEVEL", "WARNING")
    app, kwargs = _captured_run(env)
    assert app == "api.main:app"
    assert kwargs["host"] == "0.0.0.0" and kwargs["port"] == 9001
    assert kwargs["workers"] == 4 and kwargs["reload"] is False
    assert kwargs["log_level"] == "warning"


def test_run_backend_reload_disables_workers(env):
    env.setenv("RELOAD", "true")
    env.setenv("WORKERS", "4")
    _, kwargs = _captured_run(env)
    assert kwargs["reload"] is True and kwargs["workers"] is None
