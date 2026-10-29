"""RV subcategory validation, RV attribute filters, rvtrader scraper, market comps."""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

API = "/api/v1"


@pytest.fixture(scope="module")
def client():
    from api.main import app
    return TestClient(app)


@pytest.fixture(autouse=True)
def clean():
    from dealr.db.inventory_repo import inventory_store
    from f1ndr.db.db import listings_store
    from sellr.utils.utils import listings_store as sellr_store
    for s in (inventory_store, listings_store, sellr_store):
        s.clear_memory()


# ---- R1: towable vs motorized validation ----

def test_towable_rejects_motorized_fields():
    from api.schemas.list_schemas import VehicleIn
    with pytest.raises(ValidationError):
        VehicleIn(subcategory="travel_trailer", mileage=12000)
    with pytest.raises(ValidationError):
        VehicleIn(subcategory="fifth_wheel", engine="V8")
    with pytest.raises(ValidationError):
        VehicleIn(subcategory="toy_hauler", chassis="ford")
    ok = VehicleIn(subcategory="travel_trailer", sleeps=6, length_ft=28,
                   dry_weight_lbs=6000, gvwr_lbs=7500, slide_outs=2,
                   hitch_type="bumper_pull", fresh_water_gal=45)
    assert ok.sleeps == 6 and ok.hitch_type == "bumper_pull"


def test_gvwr_must_cover_dry_weight():
    from api.schemas.list_schemas import VehicleIn
    with pytest.raises(ValidationError):
        VehicleIn(subcategory="travel_trailer", dry_weight_lbs=9000, gvwr_lbs=8000)
    assert VehicleIn(subcategory="travel_trailer", dry_weight_lbs=6000, gvwr_lbs=7500)


def test_motorized_keeps_engine_chassis_mileage():
    from api.schemas.list_schemas import VehicleIn
    v = VehicleIn(subcategory="motorhome_a", mileage=55000, engine="diesel", chassis="freightliner")
    assert v.mileage == 55000 and v.engine == "diesel"


# ---- R2: RV attribute filters ----

async def test_rv_filters_search_unified_sellr_dealr(client, headers_for):
    from f1ndr.db.db import save_scraped_listings
    from sellr.utils.utils import listings_store as sellr_store

    await save_scraped_listings(
        [{"title": "2021 Grand Design Fifth Wheel", "price_value": 55000.0,
          "url": "https://www.rvtrader.com/listing/123", "sleeps": 6,
          "length_ft": 32, "dry_weight_lbs": 8000, "slide_outs": 3,
          "hitch_type": "fifth_wheel"}],
        platform="rvtrader", category="vehicles", region="calgary")

    r = client.post(f"{API}/f1ndr/search", json={"sleeps_min": 5})
    assert all(l["sleeps"] >= 5 for l in r.json()["data"]["results"]) and r.json()["data"]["results"]

    r = client.get(f"{API}/listings/unified", params={"sleeps_min": 5, "hitch_type": "fifth_wheel"})
    assert len(r.json()["data"]) == 1
    assert client.get(f"{API}/listings/unified", params={"sleeps_min": 8}).json()["data"] == []

    await sellr_store.upsert({"id": "s-rv", "title": "Trailer", "sleeps": 2,
                              "hitch_type": "bumper_pull", "category": "vehicles",
                              "status": "active", "user_id": "u-s"})
    h = headers_for("user")
    r = client.get(f"{API}/sellr/listings", params={"sleeps_min": 2}, headers=h)
    assert any(l["id"] == "s-rv" for l in r.json()["data"])
    r = client.get(f"{API}/sellr/listings", params={"sleeps_min": 4}, headers=h)
    assert all(l["id"] != "s-rv" for l in r.json()["data"])

    dealer = headers_for("dealer")
    inv = client.post(f"{API}/dealr/inventory", headers=dealer,
                      json={"name": "Dealer TT", "category": "vehicles",
                            "subcategory": "travel_trailer", "sleeps": 8,
                            "hitch_type": "bumper_pull", "status": "active"})
    assert inv.status_code == 201, inv.text
    r = client.get(f"{API}/dealr/inventory", params={"sleeps_min": 6}, headers=dealer)
    assert any(l.get("name") == "Dealer TT" for l in r.json()["data"])
    r = client.get(f"{API}/dealr/inventory", params={"sleeps_min": 10}, headers=dealer)
    assert all(l.get("name") != "Dealer TT" for l in r.json()["data"])


# ---- R3: rvtrader scraper ----

def test_rvtrader_registered_and_infers():
    from scrapers.module import SCRAPER_CLASSES
    from scrapers.rvtrader_scraper import RVTraderScraper
    from scrapers.config.regions_config import platforms_for_region
    from listr.config.config import get_listr_config

    assert SCRAPER_CLASSES["rvtrader"] is RVTraderScraper
    assert "rvtrader" in platforms_for_region("calgary")
    assert "rvtrader" in platforms_for_region("halifax")
    assert "rvtrader" in get_listr_config()["supported_platforms"]

    s = RVTraderScraper()
    listing = {"url": "https://www.rvtrader.com/listing/fifth-wheel-123", "title": "2021 Fifth Wheel RV"}
    assert s.classify_listing(listing) == "vehicles"
    assert s.infer_subcategory(listing) == "fifth_wheel"
    kijiji_rv = {"url": "https://www.kijiji.ca/v-rv-camper-travel-trailer/1", "title": "Camper"}
    assert s.infer_subcategory(kijiji_rv) == "travel_trailer"


# ---- P1-P4: market comps + pricing endpoint ----

async def test_estimate_market_price_comps():
    from f1ndr.intelligence.market import estimate_market_price

    listing = {"id": "mine", "category": "vehicles", "subcategory": "car",
               "make": "Honda", "model": "Civic", "year": 2020, "region": "calgary"}
    corpus = [
        {"id": f"c{i}", "category": "vehicles", "subcategory": "car", "make": "Honda",
         "model": "Civic", "year": 2020, "price": p, "region": "calgary"}
        for i, p in enumerate([10000, 11000, 12000, 13000])
    ] + [{"id": "old", "category": "vehicles", "subcategory": "car", "make": "Honda",
          "model": "Civic", "year": 2010, "price": 5000, "region": "calgary"}]  # year too far

    r = await estimate_market_price(listing, corpus=corpus)
    assert r["comp_count"] == 4 and r["median"] == 11500
    assert r["p25"] and r["p75"] and r["confidence"] == "medium"
    assert len(r["comparables"]) == 4

    empty = await estimate_market_price({"category": "goods", "title": "x"}, corpus=corpus)
    assert empty["comp_count"] == 0 and empty["median"] is None and empty["market_value"] is None


async def test_dealr_pricing_endpoint(client, headers_for):
    from f1ndr.db.db import save_scraped_listings

    await save_scraped_listings(
        [{"title": "Honda Civic", "price_value": float(p),
          "url": f"https://www.kijiji.ca/v-cars-trucks/calgary/civic/{p}",
          "make": "Honda", "model": "Civic", "year": 2020}
         for p in (10000, 11000, 12000, 13000)],
        platform="kijiji", category="vehicles", region="calgary")

    r = client.post(f"{API}/dealr/pricing", headers=headers_for("dealer"),
                    json={"category": "vehicles", "subcategory": "car", "make": "Honda",
                          "model": "Civic", "year": 2020, "region": "calgary"})
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["comp_count"] == 4 and data["median"] == 11500 and data["comparables"]
