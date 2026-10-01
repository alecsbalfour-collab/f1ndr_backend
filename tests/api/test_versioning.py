"""
API versioning: the API lives under /api/v1, health probes stay at the root, and the old
unversioned paths still work as hidden, deprecated aliases that point at their successor.
"""

import pytest
from fastapi.testclient import TestClient

from api.middleware.deprecation_middleware import LEGACY_DEPRECATED_AT


@pytest.fixture(scope="module")
def client():
    from api.main import app
    return TestClient(app)


def test_v1_routes_are_not_marked_deprecated(client):
    response = client.get("/api/v1/dealr/status")
    assert response.status_code == 200 and response.json()["success"] is True
    assert "Deprecation" not in response.headers and "Link" not in response.headers


@pytest.mark.parametrize("path", ["/dealr/status", "/version/", "/trinn/status", "/listings/unified"])
def test_legacy_paths_still_work_but_are_deprecated(client, path):
    response = client.get(path)
    assert response.status_code == 200 and response.json()["success"] is True
    assert response.headers["Deprecation"] == f"@{LEGACY_DEPRECATED_AT}"
    assert response.headers["Link"] == f'</api/v1{path}>; rel="successor-version"'


def test_legacy_error_responses_are_also_marked(client, headers_for):
    response = client.post("/sellr/listings", json={}, headers=headers_for())
    assert response.status_code == 422 and response.json()["error_code"] == "VALIDATION_ERROR"
    assert response.headers["Link"] == '</api/v1/sellr/listings>; rel="successor-version"'


def test_legacy_write_roundtrips_with_v1(client, headers_for):
    created = client.post("/sellr/listings", json={"title": "Civic", "price": 7500}, headers=headers_for()).json()["data"]
    assert client.get(f"/api/v1/sellr/listings/{created['id']}").json()["data"]["title"] == "Civic"


def test_health_is_root_only_and_not_deprecated(client):
    response = client.get("/health")
    assert response.status_code == 200 and "Deprecation" not in response.headers
    assert client.get("/api/v1/health").status_code == 404


def test_unknown_paths_are_not_marked_deprecated(client):
    response = client.get("/nope")
    assert response.status_code == 404 and "Deprecation" not in response.headers


def test_openapi_lists_only_versioned_api_and_health(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert "/api/v1/auth/login" in paths and {"/health", "/health/live", "/health/ready"} <= paths.keys()
    assert all(p.startswith(("/api/v1/", "/health")) for p in paths), sorted(paths)


def test_login_rate_limit_is_shared_between_legacy_and_v1(client):
    body = {"email": "nobody@example.com", "password": "x"}
    statuses = [client.post(path, json=body).status_code for path in ["/auth/login", "/api/v1/auth/login"] * 3]
    assert statuses[:5] == [401] * 5 and statuses[5] == 429


def test_cors_exposes_deprecation_headers(client):
    response = client.get("/dealr/status", headers={"Origin": "http://localhost:3000"})
    exposed = response.headers["access-control-expose-headers"].lower()
    assert "deprecation" in exposed and "link" in exposed
