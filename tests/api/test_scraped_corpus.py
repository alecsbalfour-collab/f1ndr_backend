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
    # Other tests' in-memory docs leak through the shared stores (unified/compare
    # merge all three), so clear all of them.
    from listr.db.listing_repo import listings_store as listr_store
    from sellr.utils.utils import listings_store as sellr_store

    for store in (listings_store, listr_store, sellr_store):
        store.clear_memory()


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
    assert len(await save_scraped_listings(raw, platform="kijiji")) == 1

    doc = await listings_store.get(scraped_listing_id("kijiji", KIJIJI_URL))
    assert doc["platform"] == "kijiji"
    assert doc["price"] == 18500.0
    assert doc["price_text"] == "$18,500"
    assert doc["region"] == "calgary"
    assert doc["category"] == "other"

    # Re-scraping the same URL refreshes one document instead of duplicating.
    first_seen = doc["first_seen_at"]
    raw[0]["price_value"] = 17500.0
    assert len(await save_scraped_listings(raw[:1], platform="kijiji")) == 1
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


@pytest.mark.asyncio
async def test_alert_matches_on_ingest_and_dedupes(monkeypatch):
    from watchr.core import core as watchr_core

    watchr_core.alerts_store.clear_memory()
    watchr_core.matches_store.clear_memory()

    sent = []

    async def fake_user(user_id):
        return {"user_id": user_id, "email": f"{user_id}@example.com"}

    async def fake_send(to, subject, body):
        sent.append((to, subject))
        return True

    monkeypatch.setattr("api.auth.accounts.get_user", fake_user)
    monkeypatch.setattr("api.auth.email.send_email", fake_send)

    alert = await watchr_core.create_alert(
        {"name": "Civics", "query": "civic", "price_max": 20000, "user_id": "u-watch"}
    )
    await watchr_core.create_alert({"name": "Boards", "query": "snowboard", "user_id": "u-watch"})

    listings = await save_scraped_listings(
        [{"title": "2019 Honda Civic", "price_value": 18500.0, "url": KIJIJI_URL, "location": "Calgary, AB"}],
        platform="kijiji",
    )
    assert await watchr_core.evaluate_listings(listings) == 1
    assert sent == [("u-watch@example.com", "f1ndr alert: 2019 Honda Civic")]

    # Re-scraping the same listing must not re-notify.
    assert await watchr_core.evaluate_listings(listings) == 0
    assert len(sent) == 1

    matches = await watchr_core.matches_store.find({"alert_id": alert["alert_id"]})
    assert len(matches) == 1
    assert matches[0]["notified"] is True
    assert matches[0]["listing"]["url"] == KIJIJI_URL

    # A listing outside the filters does not match.
    expensive = await save_scraped_listings(
        [{"title": "2019 Honda Civic Si", "price_value": 32000.0, "url": KIJIJI_URL + "x"}],
        platform="kijiji",
    )
    assert await watchr_core.evaluate_listings(expensive) == 0


@pytest.mark.asyncio
async def test_price_drop_renotifies(monkeypatch):
    from watchr.core import core as watchr_core

    watchr_core.alerts_store.clear_memory()
    watchr_core.matches_store.clear_memory()

    sent = []

    async def fake_user(user_id):
        return {"user_id": user_id, "email": f"{user_id}@example.com"}

    async def fake_send(to, subject, body):
        sent.append((to, subject))
        return True

    monkeypatch.setattr("api.auth.accounts.get_user", fake_user)
    monkeypatch.setattr("api.auth.email.send_email", fake_send)

    await watchr_core.create_alert({"name": "Civics", "query": "civic", "user_id": "u-price"})

    await save_scraped_listings(
        [{"title": "Honda Civic", "price_value": 18500.0, "url": KIJIJI_URL}], platform="kijiji"
    )
    assert await watchr_core.evaluate_listings(
        await listings_store.find({"platform": "kijiji"})
    ) == 1

    # Same listing re-scraped cheaper -> price-drop email, record updated.
    await save_scraped_listings(
        [{"title": "Honda Civic", "price_value": 16000.0, "url": KIJIJI_URL}], platform="kijiji"
    )
    assert await watchr_core.evaluate_listings(
        await listings_store.find({"platform": "kijiji"})
    ) == 0
    assert sent[-1] == ("u-price@example.com", "f1ndr price drop: Honda Civic")

    record = await watchr_core.matches_store.get(
        (await watchr_core.matches_store.find({"user_id": "u-price"}))[0]["id"]
    )
    assert record["previous_price"] == 18500.0
    assert record["listing"]["price"] == 16000.0
    assert record["price_dropped_at"]

    # Same price again -> no notification.
    assert await watchr_core.evaluate_listings(
        await listings_store.find({"platform": "kijiji"})
    ) == 0
    assert len(sent) == 2


@pytest.mark.asyncio
async def test_matches_route_scoped_to_user(client, headers_for):
    from watchr.core import core as watchr_core

    watchr_core.alerts_store.clear_memory()
    watchr_core.matches_store.clear_memory()

    headers = headers_for("user", sub="watcher-1")
    resp = client.post(f"{API}/watchr/alerts", json={"name": "civics", "query": "civic"}, headers=headers)
    assert resp.status_code == 201

    await watchr_core.evaluate_listings(
        await save_scraped_listings(
            [{"title": "Honda Civic", "price_value": 9000.0, "url": KIJIJI_URL + "/m"}],
            platform="kijiji",
        )
    )

    mine = client.get(f"{API}/watchr/matches", headers=headers).json()
    assert mine["data"][0]["alert_name"] == "civics"
    assert mine["data"][0]["listing"]["url"] == KIJIJI_URL + "/m"

    other = client.get(f"{API}/watchr/matches", headers=headers_for("user", sub="watcher-2")).json()
    assert other["data"] == []


def test_alert_matching_rules():
    from watchr.core.core import _alert_matches

    alert = {"status": "active", "query": "civic", "region": "calgary", "price_max": 20000}
    listing = {"title": "Honda Civic", "price": 10000, "region": "calgary", "location": "Calgary, AB"}

    assert _alert_matches(alert, listing)
    assert _alert_matches({**alert, "make": "honda"}, listing)  # make found in the text blob
    assert not _alert_matches({**alert, "status": "paused"}, listing)
    assert not _alert_matches({**alert, "region": "edmonton"}, listing)
    assert not _alert_matches({**alert, "price_max": 5000}, listing)
    assert not _alert_matches({**alert, "make": "toyota"}, listing)
    assert not _alert_matches({"status": "active"}, listing)  # no filters = not configured
    assert not _alert_matches({"status": "active", "query": "civic", "location": "edmonton"}, listing)


FB_URL = "https://www.facebook.com/marketplace/item/77"


@pytest.mark.asyncio
async def test_comparison_groups_endpoint(client):
    await save_scraped_listings(
        [{"title": "2019 Honda Civic LX Sedan", "price_value": 18500.0, "url": KIJIJI_URL, "location": "Calgary, AB"}],
        platform="kijiji",
    )
    await save_scraped_listings(
        [
            {"title": "Honda Civic LX 2019 sedan", "price_value": 17800.0, "url": FB_URL, "location": "Calgary"},
            {"title": "Snowboard bindings", "price_value": 120.0, "url": FB_URL + "x"},
            {"title": "Honda Civic LX 2019", "price_value": 40000.0, "url": FB_URL + "y"},
        ],
        platform="facebook",
    )

    resp = client.get(f"{API}/listings/compare").json()
    groups = resp["data"]
    assert len(groups) == 1  # far-priced twin and unrelated item stay out
    group = groups[0]
    assert group["count"] == 2
    assert set(group["platforms"]) == {"kijiji", "facebook"}
    assert group["min_price"] == 17800.0
    assert group["price_spread"] == 700.0

    scoped = client.get(
        f"{API}/listings/compare",
        params={"listing_id": scraped_listing_id("facebook", FB_URL)},
    ).json()
    assert len(scoped["data"]) == 1

    miss = client.get(f"{API}/listings/compare", params={"listing_id": "nope"}).json()
    assert miss["data"] == []


def test_listings_equivalent_rules():
    from f1ndr.utils.utils import listings_equivalent

    a = {"id": "1", "title": "2019 Honda Civic LX", "price": 18500.0, "category": "vehicles",
         "region": "calgary", "year": 2019}
    b = {"id": "2", "title": "Honda Civic LX 2019", "price": 17800.0, "category": "vehicles",
         "region": "calgary"}

    assert listings_equivalent(a, b)
    assert not listings_equivalent(a, {**b, "price": 30000.0})          # outside price delta
    assert not listings_equivalent(a, {**b, "region": "edmonton"})      # different market
    assert not listings_equivalent(a, {**b, "category": "goods"})       # different vertical
    assert not listings_equivalent(a, {**b, "year": 2020})              # conflicting structured field
    assert not listings_equivalent(a, {**b, "title": "Snowboard bindings"})
