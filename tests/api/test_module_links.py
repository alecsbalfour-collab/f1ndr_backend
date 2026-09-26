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
def test_endpoints(client, method, path, body, expected):
    kwargs = {"json": body} if body is not None else {}
    response = getattr(client, method)(path, **kwargs)
    assert response.status_code == expected, response.text
    payload = response.json()
    assert payload.get("success", True) is not False, payload


def test_sellr_keeps_price_when_market_value_unknown(client):
    response = client.post("/sellr/listings", json={"title": "Civic", "price": 7500})
    assert response.json()["data"]["price"] == 7500
