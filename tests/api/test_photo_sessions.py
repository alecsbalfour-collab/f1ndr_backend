"""Send-to-phone photo sessions: token-capability upload, expiry, ownership, attach."""

import base64

import pytest
from fastapi.testclient import TestClient

API = "/api/v1"
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 64
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


@pytest.fixture(scope="module")
def client():
    from api.main import app
    return TestClient(app)


def _session(client, headers, body=None):
    resp = client.post(f"{API}/sellr/photo-sessions", json=body or {}, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]


def _token(session_data):
    return session_data["phone_url"].rsplit("/", 1)[1]


def _upload(client, token, body=JPEG, content_type="image/jpeg"):
    return client.post(
        f"{API}/sellr/photo-upload/{token}", content=body, headers={"Content-Type": content_type}
    )


def test_session_lifecycle(client, headers_for):
    headers = headers_for("user", sub="photo-u1")
    data = _session(client, headers)
    assert data["status"] == "open" and data["expires_at"] and data["phone_url"]
    token = _token(data)

    resp = _upload(client, token)
    assert resp.status_code == 200, resp.text
    photo = resp.json()["data"]
    assert photo["content_type"] == "image/jpeg" and photo["size"] == len(JPEG) and photo["url"]

    polled = client.get(f"{API}/sellr/photo-sessions/{data['session_id']}", headers=headers).json()["data"]
    assert [p["id"] for p in polled["photos"]] == [photo["id"]]

    closed = client.post(
        f"{API}/sellr/photo-sessions/{data['session_id']}/close", headers=headers
    ).json()["data"]
    assert closed["status"] == "closed"
    assert _upload(client, token).status_code == 409


def test_upload_requires_live_token(client, headers_for):
    assert _upload(client, "dead-token").status_code == 404


def test_mismatched_media_type_rejected(client, headers_for):
    data = _session(client, headers_for("user", sub="photo-mt"))
    token = _token(data)
    assert _upload(client, token, body=JPEG, content_type="image/png").status_code == 415
    assert _upload(client, token, body=b"plain text", content_type="text/plain").status_code == 415
    assert _upload(client, token, body=PNG, content_type="image/png").status_code == 200


def test_oversize_rejected(client, headers_for, monkeypatch):
    monkeypatch.setenv("PHOTO_MAX_BYTES", "10")
    data = _session(client, headers_for("user", sub="photo-big"))
    assert _upload(client, _token(data)).status_code == 413


def test_session_full(client, headers_for, monkeypatch):
    monkeypatch.setenv("PHOTO_SESSION_MAX_PHOTOS", "1")
    data = _session(client, headers_for("user", sub="photo-full"))
    token = _token(data)
    assert _upload(client, token).status_code == 200
    assert _upload(client, token).status_code == 409


def test_expired_session_rejects_uploads(client, headers_for, monkeypatch):
    monkeypatch.setenv("PHOTO_SESSION_TTL_MINUTES", "0")
    headers = headers_for("user", sub="photo-exp")
    data = _session(client, headers)
    assert _upload(client, _token(data)).status_code == 410
    polled = client.get(f"{API}/sellr/photo-sessions/{data['session_id']}", headers=headers).json()["data"]
    assert polled["status"] == "expired"


def test_phone_page_and_dead_link(client, headers_for):
    data = _session(client, headers_for("user", sub="photo-page"))
    page = client.get(f"{API}/sellr/photo-upload/{_token(data)}")
    assert page.status_code == 200 and "text/html" in page.headers["content-type"]
    assert client.get(f"{API}/sellr/photo-upload/dead-token").status_code == 410


def test_session_and_photo_owner_only(client, headers_for):
    owner = headers_for("user", sub="photo-own")
    other = headers_for("user", sub="photo-other")
    data = _session(client, owner)
    photo = _upload(client, _token(data)).json()["data"]

    for method in ("get", "post"):
        resp = getattr(client, method)(
            f"{API}/sellr/photo-sessions/{data['session_id']}" + ("/close" if method == "post" else ""),
            headers=other,
        )
        assert resp.status_code == 404
    assert client.get(f"{API}/sellr/photos/{photo['id']}", headers=other).status_code == 404

    fetched = client.get(f"{API}/sellr/photos/{photo['id']}", headers=owner).json()["data"]
    assert base64.b64decode(fetched["data_b64"]) == JPEG


def test_session_routes_require_auth(client):
    assert client.post(f"{API}/sellr/photo-sessions", json={}).status_code == 401
    assert client.get(f"{API}/sellr/photo-sessions/x").status_code == 401
    assert client.post(f"{API}/sellr/photo-sessions/x/close").status_code == 401
    assert client.get(f"{API}/sellr/photos/x").status_code == 401


def test_listing_attach_and_cross_owner_guard(client, headers_for):
    owner = headers_for("user", sub="photo-att")
    other = headers_for("user", sub="photo-att2")
    data = _session(client, owner)
    photo = _upload(client, _token(data)).json()["data"]

    created = client.post(
        f"{API}/sellr/listings",
        json={"title": "Civic", "price": 7000, "category": "vehicles", "photos": [photo["id"]]},
        headers=owner,
    ).json()["data"]
    assert created["photos"] == [photo["id"]]

    # Another user cannot reference someone else's photo in their listing.
    resp = client.post(
        f"{API}/sellr/listings",
        json={"title": "X", "price": 1, "category": "goods", "photos": [photo["id"]]},
        headers=other,
    )
    assert resp.status_code == 400
    # Nor can the owner reference a photo id that does not exist.
    assert client.post(
        f"{API}/sellr/listings",
        json={"title": "Y", "price": 1, "category": "goods", "photos": ["nope"]},
        headers=owner,
    ).status_code == 400
