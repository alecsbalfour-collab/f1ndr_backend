import asyncio

import pytest

from scrapers import module
from scrapers.config.settings_config import ScraperConfig


def test_every_platform_has_a_unique_source_name():
    sources = [cls.source_name for cls in module.SCRAPER_CLASSES.values()]
    assert "base" not in sources
    assert len(sources) == len(set(sources))


async def test_run_all_limits_concurrency_and_aggregates(monkeypatch):
    active = {"now": 0, "peak": 0}

    async def fake_run(self, query=None):
        active["now"] += 1
        active["peak"] = max(active["peak"], active["now"])
        await asyncio.sleep(0.01)
        active["now"] -= 1
        ok = self.source_name != "ebay"
        return {"source": self.source_name, "success": ok, "count": 2 if ok else 0,
                "results": [], "error": None if ok else "blocked"}

    monkeypatch.setattr(module.BaseScraper, "run", fake_run)
    result = await module.run_all("civic", config=ScraperConfig(max_concurrency=2))

    assert active["peak"] == 2
    assert result["platforms"] == list(module.SCRAPER_CLASSES)
    assert result["failed"] == ["ebay"]
    assert result["total"] == 2 * (len(module.SCRAPER_CLASSES) - 1)


async def test_run_all_rejects_unknown_platforms():
    with pytest.raises(ValueError, match="nope"):
        await module.run_all("x", platforms=["ebay", "nope"])


def test_health_report_status_reflects_open_circuits():
    assert module.health_report()["status"] == "ok"
    breaker = module.EbayScraper().breaker
    for _ in range(breaker.failure_threshold):
        breaker.record_failure()
    report = module.health_report()
    assert report["status"] == "degraded"
    assert report["platforms"]["ebay"]["circuit"]["state"] == "open"
