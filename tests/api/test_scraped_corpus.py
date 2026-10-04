"""Scraped listings persist into the f1ndr corpus and surface in search/unified/raw."""

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.router_api import API_V1_PREFIX
from f1ndr.db.db import listings_store, save_scraped_listings, scraped_listing_id
from scrapers.config.settings_config import ScraperConfig
from scrapers.db.scrapers_db_connection import get_scrapers_db
from scrapers.kijiji_scraper import KijijiScraper

API = API_V1_PREFIX


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def clean_corpus():
    listings_store.clear_memory()


KIJIJI_URL = "https://www.kijiji.ca/v-cars-trucks/calgary/honda-civic/12345"
EDMONTON_URL = "https://www.realtor.ca/edmonton/house/999"


@pytest.mark.asyncio
async def test_scraped_listings_persist_and_dedupe():
    raw = [
        {
            "title": "2019 Honda Civic",
            "price": "$18,500",
            "price_value": 18500.0,
            "url": KIJIJI_URL,
            "location": "Calgary, AB",
        },
        {"title": "missing url gets skipped"},
    ]
    assert await save_scraped_listings(raw, platform="kijiji") == 1

    doc = await listings_store.get(scraped_listing_id("kijiji", KIJIJI_URL))
    assert doc["platform"] == "kijiji"
    assert doc["price"] == 18500.0
    assert doc["price_text"] == "$18,500"
    assert doc["region"] == "calgary"
    assert doc["category"] == "other"

    # Re-scraping the same URL refreshes one document instead of duplicating.
    first_seen = doc["first_seen_at"]
    raw[0]["price_value"] = 17500.0
    assert await save_scraped_listings(raw[:1], platform="kijiji") == 1
    docs = await listings_store.find({"platform": "kijiji"})
    assert len(docs) == 1
    assert docs[0]["price"] == 17500.0
    assert docs[0]["first_seen_at"] == first_seen


@pytest.mark.asyncio
async def test_scraper_run_persists_to_corpus(monkeypatch):
    html = """
    <div data-testid="listing-card">
      <a data-testid="listing-link" href="/v-cars-trucks/calgary/honda-civic/12345">
        <span data-testid="listing-title">2019 Honda Civic</span>
        <span data-testid="listing-price">$18,500</span>
        <span data-testid="listing-location">Calgary, AB</span>
      </a>
    </div>
    """
    scraper = KijijiScraper(ScraperConfig(cache_ttl_seconds=0))

    async def fake_fetch(url):
        return html

    monkeypatch.setattr(scraper, "fetch_html", fake_fetch)
    result = await scraper.run("civic")

    assert result["success"] and result["count"] == 1
    docs = await listings_store.find({"platform": "kijiji"})
    assert len(docs) == 1
    doc = docs[0]
    assert doc["title"] == "2019 Honda Civic"
    assert doc["price"] == 18500.0
    assert doc["url"].startswith("https://www.kijiji.ca/v-cars")
    assert doc["region"] == "calgary"
    assert doc["scraped_at"]


@pytest.mark.asyncio
async def test_corpus_surfaces_in_unified_raw_and_search(client):
    await save_scraped_listings(
        [{"title": "2019 Honda Civic", "price_value": 18500.0, "url": KIJIJI_URL, "location": "Calgary, AB"}],
        platform="kijiji",
    )
    await save_scraped_listings(
        [{"title": "3-bed house", "price_value": 450000.0, "url": EDMONTON_URL, "location": "Edmonton, AB"}],
        platform="realtor",
        category="real_estate",
        region="edmonton",
    )

    # listr docs from other tests share the in-memory store, so assert membership.
    raw = client.get(f"{API}/listings/raw/kijiji").json()
    assert all(d["platform"] == "kijiji" for d in raw["data"])
    assert KIJIJI_URL in {d["url"] for d in raw["data"]}

    unified = client.get(f"{API}/listings/unified").json()
    urls = {d["url"] for d in unified["data"]}
    assert {KIJIJI_URL, EDMONTON_URL} <= urls

    by_region = client.get(f"{API}/listings/unified", params={"region": "edmonton"}).json()
    assert [d["url"] for d in by_region["data"]] == [EDMONTON_URL]

    by_location = client.get(f"{API}/listings/unified", params={"location": "calgary"}).json()
    assert all("calgary" in (d.get("location") or "").lower() for d in by_location["data"])
    assert KIJIJI_URL in {d["url"] for d in by_location["data"]}

    search = client.post(f"{API}/f1ndr/search", json={"text": "civic"}).json()
    assert [r["title"] for r in search["data"]["results"]] == ["2019 Honda Civic"]
    assert search["data"]["results"][0]["platform"] == "kijiji"

    region_search = client.post(f"{API}/f1ndr/search", json={"region": "edmonton"}).json()
    results = region_search["data"]["results"]
    assert len(results) == 1 and results[0]["category"] == "real_estate"


def test_get_scrapers_db_returns_handle():
    assert get_scrapers_db() is not None
