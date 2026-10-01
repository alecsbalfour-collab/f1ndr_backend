"""dealr.tests.conftest — Shared pytest fixtures and environment setup."""

import os

import pytest


def pytest_configure(config: pytest.Config) -> None:
    """Set required env vars before any module is imported."""
    os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-pytest-only")
    # No MONGODB_URI default: it leaked to the whole session and pointed the Mongo integration tests
    # at the developer's own container. Those tests run only when MONGODB_URI is set explicitly.


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"
