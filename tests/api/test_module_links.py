"""
Smoke tests: every feature module imports, honours the shared contract,
and is reachable end-to-end through the mounted FastAPI app.
"""

import importlib
import inspect

import pytest
from fastapi.testclient import TestClient

MODULES = ["f1ndr", "trinn", "sellr", "listr", "dealr", "watchr"]
VIN = "1HGCM82633A004352"


@pytest.fixture(scope="module")
def client():
    from api.main import app
    return TestClient(app)


@pytest.fixture(scope="module")
def auth_headers(headers_for):
    return headers_for("admin")


@pytest.mark.parametrize("name", MODULES)
def test_module_contract(name):
    pkg = importlib.import_module(name)
    assert inspect.iscoroutinefunction(pkg.run)
    assert list(inspect.signature(pkg.run).parameters) == ["action", "data"]
    config = getattr(pkg, f"get_{name}_config")()
    assert isinstance(config, dict)
    assert config["feature_key"] == name
    assert {"feature_version", "enabled"} <= config.keys()


@pytest.mark.parametrize("name", MODULES)
async def test_module_rejects_unknown_action(name):
    pkg = importlib.import_module(name)
    with pytest.raises(ValueError):
        await pkg.run("not-an-action", {})


@pytest.mark.parametrize("entrypoint", ["api.main", "run_backend", "module", "api_router"])
def test_entrypoints_import(entrypoint):
    importlib.import_module(entrypoint)


@pytest.mark.parametrize(
    "method,path,body,expected",
    [
        ("get", "/api/v1/f1ndr/status", None, 200),
        ("post", "/api/v1/f1ndr/search", {"make": "Honda"}, 200),
        ("post", "/api/v1/f1ndr/intelligence", {"title": "2003 Honda Accord", "price": 5000}, 200),
        ("get", "/api/v1/trinn/status", None, 200),
        ("get", "/api/v1/trinn/config", None, 200),
        ("post", "/api/v1/trinn/schedule", {"task": "vin", "vin": VIN, "interval": 1}, 200),
        ("get", "/api/v1/sellr/status", None, 200),
        ("post", "/api/v1/sellr/listings", {"title": "2003 Honda Accord", "price": 5000, "category": "vehicles"}, 201),
        ("get", "/api/v1/listr/status", None, 200),
        ("get", "/api/v1/listr/platforms", None, 200),
        ("post", "/api/v1/listr/listings?platform=kijiji", {"title": "Accord", "category": "vehicles"}, 201),
        ("put", "/api/v1/listr/listings/abc?platform=kijiji", {"title": "Accord"}, 200),
        ("get", "/api/v1/dealr/status", None, 200),
        ("post", "/api/v1/dealr/inventory", {"name": "Lot A", "category": "vehicles"}, 201),
        ("put", "/api/v1/dealr/inventory/inv1", {"name": "Lot A"}, 200),
    ],
)
def test_endpoints(client, auth_headers, method, path, body, expected):
    kwargs = {"json": body} if body is not None else {}
    response = getattr(client, method)(path, headers=auth_headers, **kwargs)
    assert response.status_code == expected, response.text
    payload = response.json()
    assert payload.get("success", True) is not False, payload


def test_sellr_listing_crud_roundtrip(client, headers_for):
    seller = headers_for("user", sub="u-crud")
    created = client.post("/api/v1/sellr/listings", json={"title": "Civic", "price": 7500, "category": "vehicles"}, headers=seller).json()["data"]
    assert created["user_id"] == "u-crud"
    listing_id = created["id"]
    assert client.get(f"/api/v1/sellr/listings/{listing_id}").json()["data"]["title"] == "Civic"
    assert client.get("/api/v1/sellr/listings?user_id=u-crud").json()["pagination"]["total"] == 1
    assert client.put(f"/api/v1/sellr/listings/{listing_id}", json={"price": 7000}, headers=seller).json()["data"]["price"] == 7000
    assert client.delete(f"/api/v1/sellr/listings/{listing_id}", headers=seller).json()["success"] is True
    assert client.get(f"/api/v1/sellr/listings/{listing_id}").json()["success"] is False


def test_dealr_inventory_crud_roundtrip(client, auth_headers):
    created = client.post("/api/v1/dealr/inventory", json={"name": "Lot CRUD", "status": "crud", "category": "vehicles"}, headers=auth_headers).json()["data"]
    assert client.get("/api/v1/dealr/inventory?status=crud", headers=auth_headers).json()["pagination"]["total"] == 1
    assert client.delete(f"/api/v1/dealr/inventory/{created['id']}", headers=auth_headers).json()["success"] is True
    assert client.delete(f"/api/v1/dealr/inventory/{created['id']}", headers=auth_headers).json()["success"] is False


@pytest.mark.parametrize(
    "method,path",
    [
        ("post", "/api/v1/dealr/inventory"),
        ("get", "/api/v1/dealr/inventory"),
        ("put", "/api/v1/dealr/inventory/inv1"),
        ("delete", "/api/v1/dealr/inventory/inv1"),
    ],
)
@pytest.mark.parametrize("token", [None, "not-a-jwt", "refresh"])
def test_dealr_inventory_requires_access_token(client, method, path, token):
    from api.routes.auth_routes import create_refresh_token
    if token == "refresh":
        token = create_refresh_token("test-user")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    kwargs = {"json": {"name": "Lot"}} if method in ("post", "put") else {}
    assert getattr(client, method)(path, headers=headers, **kwargs).status_code == 401


def test_dealr_status_is_public(client):
    assert client.get("/api/v1/dealr/status").status_code == 200


def test_cors_preflight_allows_browser_origin(client):
    response = client.options(
        "/api/v1/dealr/inventory",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] in ("*", "http://localhost:3000")


def test_cors_production_origins(monkeypatch):
    from fastapi import FastAPI
    from api.config.cors_config import apply_cors
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("CORS_ORIGINS", "https://dealr.example.com")
    app = FastAPI()
    app.get("/ping")(lambda: {"ok": True})
    apply_cors(app)
    c = TestClient(app)
    allowed = lambda o: c.get("/ping", headers={"Origin": o}).headers.get("access-control-allow-origin")
    assert allowed("https://dealr.example.com") == "https://dealr.example.com"
    assert allowed("http://localhost:5173") == "http://localhost:5173"
    assert allowed("https://shop.flutterflow.app") == "https://shop.flutterflow.app"
    assert allowed("https://dealrlink.com") == "https://dealrlink.com"
    assert allowed("https://www.dealrlink.com") == "https://www.dealrlink.com"
    assert allowed("http://dealrlink.com") is None
    assert allowed("https://dealrlink.com.evil.io") is None
    assert allowed("https://f1ndr.ca") == "https://f1ndr.ca"
    assert allowed("https://app.f1ndr.ca") == "https://app.f1ndr.ca"
    assert allowed("https://f1ndr.ca.evil.io") is None
    assert allowed("https://evil.com") is None
    assert allowed("https://evil.com.flutterflow.app.attacker.io") is None


def test_sellr_keeps_price_when_market_value_unknown(client, auth_headers):
    response = client.post("/api/v1/sellr/listings", json={"title": "Civic", "price": 7500, "category": "vehicles"}, headers=auth_headers)
    assert response.json()["data"]["price"] == 7500


def test_watchr_alerts_persisted_per_user(client, headers_for):
    alice = headers_for("user", sub="u-alice-watchr")
    bob = headers_for("user", sub="u-bob-watchr")

    created = client.post(
        "/api/v1/watchr/alerts",
        json={"name": "Accords under 10k", "make": "Honda", "price_max": 10000},
        headers=alice,
    )
    assert created.status_code == 201, created.text
    alert = created.json()["data"]
    assert alert["user_id"] == "u-alice-watchr" and alert["alert_id"]

    assert client.get("/api/v1/watchr/alerts", headers=alice).json()["pagination"]["total"] == 1
    assert client.get("/api/v1/watchr/alerts", headers=bob).json()["pagination"]["total"] == 0
    # Non-owner delete is a 404, not a silent success.
    assert client.delete(f"/api/v1/watchr/alerts/{alert['alert_id']}", headers=bob).status_code == 404
    assert client.delete(f"/api/v1/watchr/alerts/{alert['alert_id']}", headers=alice).json()["success"] is True
    assert client.get("/api/v1/watchr/alerts", headers=alice).json()["pagination"]["total"] == 0


def test_watchr_subscriptions_roundtrip(client, headers_for):
    headers = headers_for("user", sub="u-subs")
    created = client.post("/api/v1/watchr/subscriptions", json={"name": "RV deals"}, headers=headers)
    assert created.status_code == 201, created.text
    sub_id = created.json()["data"]["subscription_id"]
    assert client.get("/api/v1/watchr/subscriptions", headers=headers).json()["pagination"]["total"] == 1
    assert client.delete(f"/api/v1/watchr/subscriptions/{sub_id}", headers=headers).json()["success"] is True
    assert client.get("/api/v1/watchr/subscriptions", headers=headers).json()["pagination"]["total"] == 0


def test_market_value_returns_null_until_pricing_lands(client):
    response = client.get(f"/api/v1/f1ndr/market/value?vin={VIN}")
    data = response.json()["data"]
    assert data["market_value"] is None


def test_vehicles_endpoint_returns_stored_listings(client, auth_headers):
    client.post(
        "/api/v1/f1ndr/intelligence",
        json={"title": "UniqueSubaruOutback99", "make": "Subaru", "model": "Outback", "price": 18000,
              "category": "vehicles", "subcategory": "car"},
        headers=auth_headers,
    )
    results = client.get("/api/v1/f1ndr/vehicles?make=Subaru").json()
    assert any(r.get("title") == "UniqueSubaruOutback99" for r in results["data"])
    # Category filter excludes non-vehicle listings.
    assert all(r.get("category") in (None, "vehicles") for r in
               client.get("/api/v1/f1ndr/vehicles?category=vehicles").json()["data"])


def test_unified_and_raw_listings_use_stored_data(client, headers_for):
    seller = headers_for("user", sub="u-unified")
    client.post("/api/v1/sellr/listings",
                json={"title": "UnifiedSofa42", "price": 250, "category": "goods"}, headers=seller)
    dealer = headers_for("dealer")
    pushed = client.post("/api/v1/listr/listings?platform=kijiji",
                         json={"title": "KijijiCanoe7", "price": 800, "category": "goods"}, headers=dealer)
    assert pushed.status_code == 201, pushed.text

    unified = client.get("/api/v1/listings/unified?search=UnifiedSofa42").json()
    assert any(r.get("title") == "UnifiedSofa42" for r in unified["data"])
    # Price filter excludes it when out of range.
    assert not any(r.get("title") == "UnifiedSofa42"
                   for r in client.get("/api/v1/listings/unified?min_price=1000").json()["data"])

    raw = client.get("/api/v1/listings/raw/kijiji").json()
    assert any(r.get("title") == "KijijiCanoe7" for r in raw["data"])
    assert all(r.get("platform") == "kijiji" for r in raw["data"])
