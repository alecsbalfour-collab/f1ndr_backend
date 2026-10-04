"""
Request/response models: bodies are validated, open-ended listing payloads keep unknown
fields but never server-managed ones, and the OpenAPI spec is complete enough to generate a client.
"""

import pytest
from fastapi.testclient import TestClient

VIN = "1HGCM82633A004352"


@pytest.fixture(scope="module")
def client():
    from api.main import app
    return TestClient(app)


@pytest.fixture(scope="module")
def auth_headers(headers_for):
    return headers_for("admin")


@pytest.fixture(scope="module")
def seller(headers_for):
    return headers_for("user", sub="schema-seller")


@pytest.mark.parametrize(
    "method,path,body",
    [
        ("post", "/api/v1/sellr/listings", {"price": 100}),
        ("post", "/api/v1/sellr/listings", {"title": "Civic"}),
        ("post", "/api/v1/sellr/listings", {"title": "Civic", "price": -1}),
        ("post", "/api/v1/sellr/listings", {"title": "Civic", "price": 100, "year": 1700}),
        ("post", "/api/v1/sellr/listings", {"title": "Civic", "price": 100, "$where": "1"}),
        ("post", "/api/v1/sellr/listings", {"title": "Civic", "price": 100, "a.b": 1}),
        ("post", "/api/v1/sellr/listings", {"title": "Civic", "price": 100, "category": "spaceship"}),
        ("post", "/api/v1/f1ndr/search", {"category": "spaceship"}),
        ("post", "/api/v1/dealr/inventory", {"category": "spaceship"}),
        ("post", "/api/v1/sellr/listings", ["not", "an", "object"]),
        ("post", "/api/v1/f1ndr/vin/decode", {"vin": "TOO-SHORT"}),
        ("post", "/api/v1/f1ndr/vin/decode", {"vin": "1HGCM82633A00435O"}),
        ("post", "/api/v1/f1ndr/search", {"year_min": 2020, "year_max": 2010}),
        ("post", "/api/v1/listr/listings?platform=myspace", {"title": "Accord"}),
        ("post", "/api/v1/trinn/run", {"task": "nope"}),
        ("post", "/api/v1/trinn/run", {"task": "scrape", "platform": "myspace"}),
        ("post", "/api/v1/trinn/schedule", {"task": "vin", "vin": VIN, "interval": 0}),
        ("post", "/api/v1/scrapers/search", {"platforms": ["myspace"]}),
        ("post", "/api/v1/watchr/alerts", {}),
        ("post", "/api/v1/auth/register", {"email": "not-an-email", "password": "Str0ng!Pass"}),
        ("post", "/api/v1/auth/login", {"email": "a@example.com"}),
        ("post", "/api/v1/auth/refresh", {}),
        ("post", "/api/v1/dealr/inventory", {"mileage": -5}),
    ],
)
def test_invalid_bodies_are_rejected(client, auth_headers, method, path, body):
    response = getattr(client, method)(path, json=body, headers=auth_headers)
    assert response.status_code == 422, response.text
    payload = response.json()
    assert payload["success"] is False and payload["error_code"] == "VALIDATION_ERROR"
    assert payload["details"]["validation_errors"]


def test_listing_keeps_extra_fields_but_not_server_managed_ones(client, seller):
    body = {"title": "Civic", "price": 7500, "color": "red", "features": ["sunroof"],
            "id": "chosen-by-client", "created_at": "1999-01-01", "_id": "x"}
    created = client.post("/api/v1/sellr/listings", json=body, headers=seller).json()["data"]
    assert created["color"] == "red" and created["features"] == ["sunroof"]
    assert created["id"] != "chosen-by-client"
    stored = client.get(f"/api/v1/sellr/listings/{created['id']}").json()["data"]
    assert stored["created_at"] != "1999-01-01" and "_id" not in stored


def test_category_defaults_to_car_and_filters(client, seller, headers_for):
    car = client.post("/api/v1/sellr/listings", json={"title": "Civic", "price": 7500}, headers=seller).json()["data"]
    rv = client.post("/api/v1/sellr/listings", json={"title": "Fifth Wheel", "price": 40000, "category": "fifth_wheel"},
                     headers=seller).json()["data"]
    assert car["category"] == "car" and rv["category"] == "fifth_wheel"

    listed = lambda c: {i["id"] for i in client.get("/api/v1/sellr/listings", params={"category": c}).json()["data"]}
    assert rv["id"] in listed("fifth_wheel") and car["id"] not in listed("fifth_wheel")
    assert car["id"] in listed("car") and rv["id"] not in listed("car")

    # Explicit null and invalid categories behave like omitting the field / a bad value.
    cleared = client.put(f"/api/v1/sellr/listings/{rv['id']}", json={"category": None}, headers=seller).json()["data"]
    assert cleared["category"] == "car"

    dealer = headers_for("dealer", sub="cat-dealer")
    item = client.post("/api/v1/dealr/inventory", json={"name": "Lot", "category": "motorcycle"}, headers=dealer).json()["data"]
    assert item["category"] == "motorcycle"
    ids = {i["id"] for i in client.get("/api/v1/dealr/inventory", params={"category": "motorcycle"}, headers=dealer).json()["data"]}
    assert item["id"] in ids
    ids = {i["id"] for i in client.get("/api/v1/dealr/inventory", params={"category": "truck"}, headers=dealer).json()["data"]}
    assert item["id"] not in ids

    seeded = client.post("/api/v1/f1ndr/intelligence", json={"title": "Toy Hauler X1", "price": 30000, "category": "toy_hauler"},
                         headers=seller)
    assert seeded.status_code == 200
    titles = lambda c: {r["title"] for r in client.post("/api/v1/f1ndr/search", json={"category": c}).json()["data"]["results"]}
    assert "Toy Hauler X1" in titles("toy_hauler") and "Toy Hauler X1" not in titles("car")


def test_partial_update_only_touches_sent_fields(client, seller):
    created = client.post("/api/v1/sellr/listings", json={"title": "Civic", "price": 7500, "make": "Honda"}, headers=seller).json()["data"]
    updated = client.put(f"/api/v1/sellr/listings/{created['id']}", json={"price": 7000, "created_at": "1999-01-01"}, headers=seller).json()["data"]
    assert updated["price"] == 7000 and updated["make"] == "Honda" and updated["title"] == "Civic"
    assert updated["created_at"] != "1999-01-01"


def test_vin_is_normalized_before_decoding(client, seller, monkeypatch):
    from api.routes import f1ndr_routes
    seen = []
    monkeypatch.setattr(f1ndr_routes, "decode_vin", lambda vin: seen.append(vin) or {"vin": vin, "valid": True})
    response = client.post("/api/v1/f1ndr/vin/decode", json={"vin": f"  {VIN.lower()} "}, headers=seller)
    assert response.status_code == 200 and seen == [VIN]


def test_success_responses_use_the_envelope(client, auth_headers):
    body = client.get("/api/v1/trinn/config", headers=auth_headers).json()
    assert body["success"] is True and body["data"]["feature_key"] == "trinn" and body["timestamp"]
    page = client.get("/api/v1/sellr/listings", params={"page_size": 1}).json()
    assert isinstance(page["data"], list) and page["pagination"]["page_size"] == 1


def test_openapi_is_complete_for_client_generation(client):
    spec = client.get("/openapi.json").json()
    operations = [(path, method, op) for path, item in spec["paths"].items() for method, op in item.items()]
    ids = [op["operationId"] for _, _, op in operations]
    assert len(ids) == len(set(ids))

    untyped_bodies, untyped_responses = [], []
    for path, method, op in operations:
        body = op.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema")
        if body is not None and "$ref" not in body and "anyOf" not in body and "oneOf" not in body:
            untyped_bodies.append(f"{method} {path}")
        for code, response in op["responses"].items():
            schema = response.get("content", {}).get("application/json", {}).get("schema")
            if code.startswith("2") and path != "/health" and not (schema and "$ref" in schema):
                untyped_responses.append(f"{method} {path} {code}")
    assert untyped_bodies == [] and untyped_responses == []

    login = spec["paths"]["/api/v1/auth/login"]["post"]
    assert login["operationId"] == "authentication_login_user"
    assert login["responses"]["422"]["content"]["application/json"]["schema"]["$ref"].endswith("/ErrorEnvelope")
    roles = spec["components"]["schemas"]["RolesUpdateRequest"]["properties"]["roles"]["items"]
    assert set(roles["enum"]) == {"user", "dealer", "admin"}
