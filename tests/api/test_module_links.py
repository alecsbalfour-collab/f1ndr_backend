"""
Smoke tests: every feature module imports, honours the shared contract,
and is reachable end-to-end through the mounted FastAPI app.
"""

import importlib
import inspect

import pytest
from fastapi.testclient import TestClient

MODULES = ["f1ndr", "trinn", "sellr", "listr", "dealr"]
VIN = "1HGCM82633A004352"


@pytest.fixture(scope="module")
def client():
    from api.main import app
    return TestClient(app)


@pytest.fixture(scope="module")
def auth_headers():
    from api.routes.auth_routes import create_access_token
    return {"Authorization": f"Bearer {create_access_token('test-user')}"}


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
        ("get", "/f1ndr/status", None, 200),
        ("post", "/f1ndr/search", {"make": "Honda"}, 200),
        ("post", "/f1ndr/intelligence", {"title": "2003 Honda Accord", "price": 5000}, 200),
        ("get", "/trinn/status", None, 200),
        ("get", "/trinn/config", None, 200),
        ("post", "/trinn/schedule", {"task": "vin", "vin": VIN, "interval": 1}, 200),
        ("get", "/sellr/status", None, 200),
        ("post", "/sellr/listings", {"title": "2003 Honda Accord", "price": 5000}, 201),
        ("get", "/listr/status", None, 200),
        ("get", "/listr/platforms", None, 200),
        ("post", "/listr/listings?platform=kijiji", {"title": "Accord"}, 201),
        ("put", "/listr/listings/abc?platform=kijiji", {"title": "Accord"}, 200),
        ("get", "/dealr/status", None, 200),
        ("post", "/dealr/inventory", {"name": "Lot A"}, 201),
        ("put", "/dealr/inventory/inv1", {"name": "Lot A"}, 200),
    ],
)
def test_endpoints(client, auth_headers, method, path, body, expected):
    kwargs = {"json": body} if body is not None else {}
    response = getattr(client, method)(path, headers=auth_headers, **kwargs)
    assert response.status_code == expected, response.text
    payload = response.json()
    assert payload.get("success", True) is not False, payload


def test_sellr_listing_crud_roundtrip(client):
    created = client.post("/sellr/listings", json={"title": "Civic", "price": 7500, "user_id": "u-crud"}).json()["data"]
    listing_id = created["id"]
    assert client.get(f"/sellr/listings/{listing_id}").json()["data"]["title"] == "Civic"
    assert client.get("/sellr/listings?user_id=u-crud").json()["data"]["total"] == 1
    assert client.put(f"/sellr/listings/{listing_id}", json={"price": 7000}).json()["data"]["price"] == 7000
    assert client.delete(f"/sellr/listings/{listing_id}").json()["success"] is True
    assert client.get(f"/sellr/listings/{listing_id}").json()["success"] is False


def test_dealr_inventory_crud_roundtrip(client, auth_headers):
    created = client.post("/dealr/inventory", json={"name": "Lot CRUD", "status": "crud"}, headers=auth_headers).json()["data"]
    assert client.get("/dealr/inventory?status=crud", headers=auth_headers).json()["pagination"]["total"] == 1
    assert client.delete(f"/dealr/inventory/{created['id']}", headers=auth_headers).json()["success"] is True
    assert client.delete(f"/dealr/inventory/{created['id']}", headers=auth_headers).json()["success"] is False


@pytest.mark.parametrize(
    "method,path",
    [
        ("post", "/dealr/inventory"),
        ("get", "/dealr/inventory"),
        ("put", "/dealr/inventory/inv1"),
        ("delete", "/dealr/inventory/inv1"),
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
    assert client.get("/dealr/status").status_code == 200


def test_cors_preflight_allows_browser_origin(client):
    response = client.options(
        "/dealr/inventory",
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
    assert allowed("https://evil.com") is None
    assert allowed("https://evil.com.flutterflow.app.attacker.io") is None


def test_sellr_keeps_price_when_market_value_unknown(client):
    response = client.post("/sellr/listings", json={"title": "Civic", "price": 7500})
    assert response.json()["data"]["price"] == 7500
