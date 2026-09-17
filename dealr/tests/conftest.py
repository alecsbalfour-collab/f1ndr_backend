"""dealr.tests.conftest — Shared pytest fixtures and environment setup."""

import os

import pytest


def pytest_configure(config: pytest.Config) -> None:
    """Set required env vars before any module is imported."""
    os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-pytest-only")
    os.environ.setdefault("MONGODB_URI",    "mongodb://localhost:27017")
    os.environ.setdefault("MONGODB_DB_NAME","dealr_tests")


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"
