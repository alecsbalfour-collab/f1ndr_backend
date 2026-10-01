"""
Auth by default: every versioned API route requires an access token unless it is listed in
PUBLIC_ROUTES. Adding a route without auth fails here until it is protected or deliberately listed.
"""

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from api.dependencies.auth import require_user
from api.main import app
from api.router_api import API_V1_PREFIX

PUBLIC_ROUTES = {
    ("GET", "/version/"),
    *{("GET", f"/{module}/status") for module in ("dealr", "sellr", "listr", "trinn", "watchr", "f1ndr")},
    # Account entry points
    ("POST", "/auth/register"),
    ("POST", "/auth/login"),
    ("POST", "/auth/refresh"),
    ("POST", "/auth/verify-email"),
    ("GET", "/auth/verify-email"),
    ("POST", "/auth/flutterflow/webhook"),  # guarded by FLUTTERFLOW_API_KEY instead of a user token
    # Anonymous browsing
    ("GET", "/f1ndr/vehicles"),
    ("POST", "/f1ndr/search"),
    ("GET", "/f1ndr/market/value"),
    ("GET", "/sellr/listings"),
    ("GET", "/sellr/listings/{listing_id}"),
    ("GET", "/listr/platforms"),
    ("GET", "/scrapers/platforms"),
    ("GET", "/listings/unified"),
    ("GET", "/listings/raw/facebook"),
    ("GET", "/listings/raw/kijiji"),
    ("GET", "/listings/raw/craigslist"),
}


def _requires_user(dependant) -> bool:
    return any(dep.call is require_user or _requires_user(dep) for dep in dependant.dependencies)


def _api_routes():
    for route in app.routes:
        if isinstance(route, APIRoute) and route.path.startswith(API_V1_PREFIX):
            for method in route.methods - {"HEAD"}:
                yield method, route.path[len(API_V1_PREFIX):], route


def test_every_api_route_is_protected_or_explicitly_public():
    unprotected = {(m, p) for m, p, r in _api_routes() if not _requires_user(r.dependant)}
    assert unprotected - PUBLIC_ROUTES == set(), "Protect these routes or add them to PUBLIC_ROUTES"
    assert PUBLIC_ROUTES - unprotected == set(), "Stale PUBLIC_ROUTES entries (route removed or now protected)"


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.mark.parametrize(
    "role,method,path,body,expected",
    [
        (None, "post", "/watchr/alerts", {"name": "a"}, 401),
        ("user", "post", "/watchr/alerts", {"name": "a"}, 201),
        ("user", "get", "/dealr/inventory", None, 403),
        ("dealer", "get", "/dealr/inventory", None, 200),
        ("user", "post", "/listr/listings?platform=kijiji", {"title": "x"}, 403),
        ("dealer", "get", "/trinn/config", None, 403),
        ("admin", "get", "/trinn/config", None, 200),
        ("dealer", "post", "/scrapers/search", {"platforms": []}, 403),
        (None, "post", "/f1ndr/intelligence", {"title": "x"}, 401),
    ],
)
def test_role_guards(client, headers_for, role, method, path, body, expected):
    kwargs = {"json": body} if body is not None else {}
    headers = headers_for(role) if role else {}
    assert getattr(client, method)(f"{API_V1_PREFIX}{path}", headers=headers, **kwargs).status_code == expected


def test_owner_comes_from_token_not_body(client, headers_for):
    alert = client.post(f"{API_V1_PREFIX}/watchr/alerts", json={"name": "a", "user_id": "someone-else"},
                        headers=headers_for("user", sub="real-owner")).json()["data"]
    assert alert["user_id"] == "real-owner"


def test_sellers_cannot_touch_each_others_listings(client, headers_for):
    alice, bob = headers_for("user", sub="alice"), headers_for("user", sub="bob")
    listing = client.post(f"{API_V1_PREFIX}/sellr/listings", json={"title": "Civic", "price": 1}, headers=alice).json()["data"]
    url = f"{API_V1_PREFIX}/sellr/listings/{listing['id']}"
    assert client.put(url, json={"price": 2}, headers=bob).status_code == 404
    assert client.delete(url, headers=bob).status_code == 404
    assert client.put(url, json={"price": 2}, headers=headers_for("admin")).status_code == 200
    assert client.delete(url, headers=alice).status_code == 200


def test_dealers_only_see_their_own_inventory(client, headers_for):
    d1, d2 = headers_for("dealer", sub="dealer-1"), headers_for("dealer", sub="dealer-2")
    item = client.post(f"{API_V1_PREFIX}/dealr/inventory", json={"name": "Lot", "status": "iso"}, headers=d1).json()["data"]
    assert item["owner_id"] == "dealer-1"
    listed = lambda h: [i["id"] for i in client.get(f"{API_V1_PREFIX}/dealr/inventory?status=iso", headers=h).json()["data"]]
    assert item["id"] in listed(d1) and item["id"] not in listed(d2)
    assert client.put(f"{API_V1_PREFIX}/dealr/inventory/{item['id']}", json={"name": "Mine"}, headers=d2).status_code == 404
    assert client.delete(f"{API_V1_PREFIX}/dealr/inventory/{item['id']}", headers=d2).status_code == 404
    assert client.delete(f"{API_V1_PREFIX}/dealr/inventory/{item['id']}", headers=d1).status_code == 200
