# scrapers/tests/conftest.py

import pytest

from scrapers.core.metrics_core import metrics_registry
from scrapers.core.resilience_core import breaker_registry
from scrapers.db.cache_db import _cache_store


@pytest.fixture
def sample_query():
    return "test"


@pytest.fixture(autouse=True)
def reset_scraper_state():
    breaker_registry.reset()
    metrics_registry.reset()
    _cache_store.clear()
    yield
    breaker_registry.reset()
    metrics_registry.reset()
    _cache_store.clear()
