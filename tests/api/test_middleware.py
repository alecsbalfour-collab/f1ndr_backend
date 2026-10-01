"""
The app-level stack: request IDs, security headers, timing, exception handlers,
rate limiting, and the single health endpoint.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    from api.main import app
    return TestClient(app)


def _assert_error_envelope(response, status_code, error_code):
    assert response.status_code == status_code, response.text
    body = response.json()
    assert body["success"] is False
    assert body["error_code"] == error_code
    assert body["request_id"] == response.headers["X-Request-ID"]
    return body


def test_every_response_gets_request_id_security_headers_and_timing(client):
    response = client.get("/api/v1/dealr/status")
    assert response.status_code == 200
    assert response.headers["X-Request-ID"]
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert float(response.headers["X-Process-Time-ms"]) >= 0


def test_inbound_request_id_is_kept_only_when_well_formed(client):
    assert client.get("/api/v1/dealr/status", headers={"X-Request-ID": "trace-abc-12345"}).headers["X-Request-ID"] == "trace-abc-12345"
    replaced = client.get("/api/v1/dealr/status", headers={"X-Request-ID": "bad id\r\ninjected"}).headers["X-Request-ID"]
    assert replaced != "bad id\r\ninjected" and len(replaced) == 36


def test_unhandled_exception_returns_generic_500_without_internals(client, monkeypatch):
    import api.routes.controllers.health_controller as health

    def boom():
        raise RuntimeError("secret connection string")

    monkeypatch.setattr(health, "health_report", boom)
    response = client.get("/health")
    body = _assert_error_envelope(response, 500, "INTERNAL_ERROR")
    assert "secret" not in response.text
    assert body["message"] == "Internal server error"
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_unknown_route_uses_error_envelope(client):
    _assert_error_envelope(client.get("/does-not-exist"), 404, "NOT_FOUND")


def test_auth_failure_keeps_www_authenticate(client):
    response = client.get("/api/v1/dealr/inventory")
    _assert_error_envelope(response, 401, "UNAUTHORIZED")
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_validation_error_does_not_echo_input(client, headers_for):
    response = client.post("/api/v1/scrapers/search", json={"query": "p4ssw0rd-" * 100}, headers=headers_for("admin"))
    body = _assert_error_envelope(response, 422, "VALIDATION_ERROR")
    assert body["details"]["validation_errors"]
    assert "p4ssw0rd" not in response.text


@pytest.mark.parametrize("path,allowed", [("/api/v1/auth/login", 5), ("/api/v1/auth/register", 3)])
def test_auth_endpoints_are_strictly_rate_limited(client, path, allowed):
    body = {"email": "nobody@example.com", "password": "x"}
    for _ in range(allowed):
        assert client.post(path, json=body).status_code != 429
    response = client.post(path, json=body)
    _assert_error_envelope(response, 429, "RATE_LIMITED")
    assert int(response.headers["Retry-After"]) > 0


def test_default_rate_limit_applies_to_other_routes(client):
    statuses = [client.get("/api/v1/version/").status_code for _ in range(101)]
    assert statuses[:100] == [200] * 100
    assert statuses[100] == 429


def test_health_is_single_endpoint_and_exempt_from_rate_limit(client):
    for _ in range(105):
        response = client.get("/health")
        assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "ok"
    assert {"trinn", "scrapers"} <= data["components"].keys()
    assert client.get("/api/v1/trinn/health").status_code == 404
    assert client.get("/api/v1/scrapers/health").status_code == 404
