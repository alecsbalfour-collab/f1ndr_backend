"""Auth flows: bcrypt storage, lockout, refresh rotation/revocation, email verification, scopes, audit."""

import asyncio
import re
from datetime import timedelta

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from jose import jwt

from api.auth import accounts, store
from api.config.settings_config import get_settings
from f1ndr.config.auth_config import auth_config

PASSWORD = "Str0ng!Pass"


@pytest.fixture
def client():
    from api.main import app
    return TestClient(app)


@pytest.fixture(autouse=True)
def clean_stores(monkeypatch):
    from api.security.rate_limiter import limiter
    # These flows log in more often than the per-IP limits allow; limits are covered in test_middleware
    monkeypatch.setattr(limiter, "enabled", False)
    store.clear_memory()
    yield
    store.clear_memory()


@pytest.fixture
def outbox(monkeypatch):
    sent = []

    async def fake_send(to, subject, body):
        sent.append({"to": to, "subject": subject, "body": body})
        return True

    monkeypatch.setattr("api.routes.auth_routes.send_email", fake_send)
    return sent


def run(coro):
    return asyncio.run(coro)


def register(client, email="alice@example.com", password=PASSWORD):
    return client.post("/api/v1/auth/register", json={"email": email, "password": password, "name": "Alice"})


def login(client, email="alice@example.com", password=PASSWORD):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


def token_from(mail):
    return re.search(r"token=([\w-]+)", mail["body"]).group(1)


def make_admin(client, email="admin@example.com"):
    user = register(client, email).json()["data"]["user"]
    run(accounts.set_roles(user["user_id"], ["user", "admin"]))
    return login(client, email).json()["data"]


def audit_events(user_id):
    return [e["event"] for e in run(store.audit_log.find({"user_id": user_id}, limit=500))]


def test_register_hashes_with_bcrypt_and_rejects_duplicates(client, outbox):
    response = register(client, "Alice@Example.com")
    assert response.status_code == 201, response.text
    data = response.json()["data"]
    assert data["user"]["email"] == "alice@example.com"
    assert data["user"]["roles"] == ["user"] and data["user"]["email_verified"] is False
    stored = run(accounts.get_user(data["user"]["user_id"]))
    assert stored["password_hash"].startswith("$2") and PASSWORD not in stored["password_hash"]
    assert register(client, "alice@EXAMPLE.com").status_code == 409
    assert len(outbox) == 1 and outbox[0]["to"] == "alice@example.com"


def test_register_rejects_weak_and_overlong_passwords(client, outbox):
    assert register(client, password="short").json()["error_code"] == "WEAK_PASSWORD"
    assert register(client, password="Aa1!" + "x" * 80).json()["error_code"] == "WEAK_PASSWORD"


def test_access_token_claims(client, outbox):
    token = register(client).json()["data"]["access_token"]
    claims = jwt.get_unverified_claims(token)
    assert claims["exp"] - claims["iat"] == auth_config.token_expiry_minutes * 60
    assert claims["roles"] == ["user"] and "listings:write" in claims["scopes"] and "audit:read" not in claims["scopes"]
    assert claims["email_verified"] is False and claims["jti"]


def test_login_success_and_failure(client, outbox):
    register(client)
    assert login(client).status_code == 200
    assert login(client, password="Wr0ng!Pass").status_code == 401
    assert login(client, email="nobody@example.com").status_code == 401


def test_lockout_after_repeated_failures_and_admin_unlock(client, outbox):
    user_id = register(client).json()["data"]["user"]["user_id"]
    for _ in range(auth_config.max_login_attempts):
        assert login(client, password="Wr0ng!Pass").status_code == 401
    locked = login(client)
    assert locked.status_code == 423 and locked.json()["error_code"] == "ACCOUNT_LOCKED"
    assert int(locked.headers["Retry-After"]) > 0
    assert {"login_failed", "account_locked", "login_blocked"} <= set(audit_events(user_id))

    admin = make_admin(client)
    assert client.post(f"/api/v1/auth/users/{user_id}/unlock", headers=bearer(admin["access_token"])).status_code == 200
    assert login(client).status_code == 200


def test_lockout_expires(client, outbox):
    user_id = register(client).json()["data"]["user"]["user_id"]
    run(store.users.update(user_id, {"locked_until": store.utcnow() - timedelta(seconds=1)}))
    assert login(client).status_code == 200


def test_successful_login_resets_failure_count(client, outbox):
    register(client)
    for _ in range(auth_config.max_login_attempts - 1):
        login(client, password="Wr0ng!Pass")
    assert login(client).status_code == 200
    login(client, password="Wr0ng!Pass")
    assert login(client).status_code == 200


def test_refresh_rotates_and_detects_reuse(client, outbox):
    first = register(client).json()["data"]["refresh_token"]
    rotated = client.post("/api/v1/auth/refresh", json={"refresh_token": first})
    assert rotated.status_code == 200, rotated.text
    second = rotated.json()["data"]["refresh_token"]
    assert second != first and rotated.json()["data"]["access_token"]

    replay = client.post("/api/v1/auth/refresh", json={"refresh_token": first})
    assert replay.status_code == 401
    # Reuse revokes the whole session, including the legitimately rotated token
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": second}).status_code == 401
    user_id = rotated.json()["data"]["user"]["user_id"]
    assert "refresh_token_reuse" in audit_events(user_id)


def test_refresh_rejects_unknown_and_access_tokens(client, outbox):
    from api.routes.auth_routes import create_refresh_token
    data = register(client).json()["data"]
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": create_refresh_token(data["user"]["user_id"])}).status_code == 401
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": data["access_token"]}).status_code == 401


def test_logout_revokes_access_and_refresh_tokens(client, outbox):
    data = register(client).json()["data"]
    headers = bearer(data["access_token"])
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 200
    assert client.post("/api/v1/auth/logout", headers=headers, json={"refresh_token": data["refresh_token"]}).status_code == 200
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 401
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": data["refresh_token"]}).status_code == 401


def test_logout_all_revokes_every_session(client, outbox):
    register(client)
    sessions = [login(client).json()["data"] for _ in range(3)]
    response = client.post("/api/v1/auth/logout-all", headers=bearer(sessions[0]["access_token"]))
    assert response.json()["data"]["sessions_revoked"] == 4
    for session in sessions:
        assert client.post("/api/v1/auth/refresh", json={"refresh_token": session["refresh_token"]}).status_code == 401


def test_session_limit_evicts_oldest(client, outbox, monkeypatch):
    monkeypatch.setattr(auth_config, "max_sessions_per_user", 2)
    oldest = register(client).json()["data"]["refresh_token"]
    newer = [login(client).json()["data"]["refresh_token"] for _ in range(2)]
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": oldest}).status_code == 401
    assert all(client.post("/api/v1/auth/refresh", json={"refresh_token": t}).status_code == 200 for t in newer)


def test_email_verification_flow(client, outbox):
    data = register(client).json()["data"]
    token = token_from(outbox[0])
    assert "/api/v1/auth/verify-email?token=" in outbox[0]["body"]
    verified = client.post("/api/v1/auth/verify-email", json={"token": token})
    assert verified.status_code == 200 and verified.json()["data"]["email_verified"] is True
    assert client.post("/api/v1/auth/verify-email", json={"token": token}).status_code == 400  # single use
    resend = client.post("/api/v1/auth/verify-email/resend", headers=bearer(data["access_token"]))
    assert resend.json()["error_code"] == "ALREADY_VERIFIED"
    assert "email_verified" in audit_events(data["user"]["user_id"])


def test_verification_link_resend_and_expiry(client, outbox):
    data = register(client).json()["data"]
    first = token_from(outbox[0])
    assert client.post("/api/v1/auth/verify-email/resend", headers=bearer(data["access_token"])).status_code == 200
    second = token_from(outbox[1])
    assert client.get("/api/v1/auth/verify-email", params={"token": first}).status_code == 400  # superseded
    for record in run(store.email_tokens.find({})):
        run(store.email_tokens.update(record["token_hash"], {"expires_at": store.utcnow() - timedelta(seconds=1)}))
    assert client.get("/api/v1/auth/verify-email", params={"token": second}).status_code == 400


def test_verification_email_uses_configured_url(client, outbox, monkeypatch):
    monkeypatch.setenv("EMAIL_VERIFICATION_URL", "https://f1ndr.ca/verify")
    get_settings.cache_clear()
    try:
        register(client)
    finally:
        get_settings.cache_clear()
    assert "https://f1ndr.ca/verify?token=" in outbox[0]["body"]


def test_admin_email_promoted_only_after_verification(client, outbox, monkeypatch):
    monkeypatch.setenv("ADMIN_EMAILS", "boss@example.com")
    get_settings.cache_clear()
    try:
        data = register(client, "boss@example.com").json()["data"]
        assert data["user"]["roles"] == ["user"]
        verified = client.post("/api/v1/auth/verify-email", json={"token": token_from(outbox[0])}).json()["data"]
    finally:
        get_settings.cache_clear()
    assert verified["roles"] == ["user", "admin"]


def test_password_reset_flow(client, outbox):
    data = register(client).json()["data"]
    # Same 200 for known and unknown emails — the endpoint can't be used to probe accounts.
    assert client.post("/api/v1/auth/password-reset/request", json={"email": "alice@example.com"}).status_code == 200
    assert client.post("/api/v1/auth/password-reset/request", json={"email": "nobody@example.com"}).status_code == 200
    reset_mail = [m for m in outbox if "password" in m["subject"].lower()][-1]
    token = token_from(reset_mail)

    # A weak password is rejected without consuming the token.
    weak = client.post("/api/v1/auth/password-reset/confirm", json={"token": token, "password": "short"})
    assert weak.json()["error_code"] == "WEAK_PASSWORD"

    done = client.post("/api/v1/auth/password-reset/confirm", json={"token": token, "password": "N3w!Passw0rd"})
    assert done.status_code == 200 and done.json()["data"]["sessions_revoked"] >= 1

    # Old password and every existing session are dead; the new password works.
    assert login(client).status_code == 401
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": data["refresh_token"]}).status_code == 401
    assert login(client, password="N3w!Passw0rd").status_code == 200
    # Single use.
    again = client.post("/api/v1/auth/password-reset/confirm", json={"token": token, "password": "N3w!Passw0rd"})
    assert again.json()["error_code"] == "INVALID_RESET_TOKEN"
    assert {"password_reset_requested", "password_reset"} <= set(audit_events(data["user"]["user_id"]))


def test_password_reset_token_purpose_and_expiry(client, outbox):
    register(client)
    # A verification token is not a reset token, and isn't consumed by the attempt.
    verified_token = token_from(outbox[0])
    wrong_purpose = client.post("/api/v1/auth/password-reset/confirm",
                                json={"token": verified_token, "password": "N3w!Passw0rd"})
    assert wrong_purpose.json()["error_code"] == "INVALID_RESET_TOKEN"
    assert client.post("/api/v1/auth/verify-email", json={"token": verified_token}).status_code == 200

    client.post("/api/v1/auth/password-reset/request", json={"email": "alice@example.com"})
    for record in run(store.email_tokens.find({"purpose": "password_reset"})):
        run(store.email_tokens.update(record["token_hash"], {"expires_at": store.utcnow() - timedelta(seconds=1)}))
    expired = client.post("/api/v1/auth/password-reset/confirm",
                          json={"token": token_from(outbox[-1]), "password": "N3w!Passw0rd"})
    assert expired.json()["error_code"] == "INVALID_RESET_TOKEN"


def test_password_reset_clears_lockout(client, outbox):
    register(client)
    for _ in range(auth_config.max_login_attempts):
        login(client, password="Wr0ng!Pass")
    assert login(client).status_code == 423
    client.post("/api/v1/auth/password-reset/request", json={"email": "alice@example.com"})
    token = token_from(outbox[-1])
    client.post("/api/v1/auth/password-reset/confirm", json={"token": token, "password": "N3w!Passw0rd"})
    assert login(client, password="N3w!Passw0rd").status_code == 200


def test_scopes_guard_admin_routes(client, outbox):
    user = register(client).json()["data"]
    headers = bearer(user["access_token"])
    assert client.get("/api/v1/auth/audit", headers=headers).status_code == 403
    assert client.put(f"/api/v1/auth/users/{user['user']['user_id']}/roles", headers=headers, json={"roles": ["admin"]}).status_code == 403

    admin = bearer(make_admin(client)["access_token"])
    audit = client.get("/api/v1/auth/audit", headers=admin, params={"event": "register"})
    assert audit.status_code == 200 and {e["event"] for e in audit.json()["data"]} == {"register"}
    assert client.put(f"/api/v1/auth/users/{user['user']['user_id']}/roles", headers=admin, json={"roles": ["root"]}).status_code == 422
    assert client.put("/api/v1/auth/users/missing/roles", headers=admin, json={"roles": ["dealer"]}).status_code == 404

    updated = client.put(f"/api/v1/auth/users/{user['user']['user_id']}/roles", headers=admin, json={"roles": ["user", "dealer"]})
    assert updated.json()["data"]["roles"] == ["user", "dealer"]
    refreshed = client.post("/api/v1/auth/refresh", json={"refresh_token": user["refresh_token"]}).json()["data"]
    assert "inventory:write" in jwt.get_unverified_claims(refreshed["access_token"])["scopes"]
    changed = run(store.audit_log.find({"event": "roles_changed"}))
    assert changed[0]["details"] == {"from": ["user"], "to": ["user", "dealer"]} and changed[0]["actor_id"] != changed[0]["user_id"]


def test_me_audit_lists_own_events(client, outbox):
    data = register(client).json()["data"]
    events = client.get("/api/v1/auth/me/audit", headers=bearer(data["access_token"])).json()["data"]
    assert {e["event"] for e in events} >= {"register", "email_verification_sent"}
    assert all(e["user_id"] == data["user"]["user_id"] for e in events)
    assert events[0]["request_id"]


def test_require_verified_email_dependency(client, outbox):
    from api.dependencies.auth import require_verified_email
    mini = FastAPI()
    mini.get("/gated", dependencies=[Depends(require_verified_email)])(lambda: {"ok": True})
    gated = TestClient(mini)

    data = register(client).json()["data"]
    headers = bearer(data["access_token"])
    assert gated.get("/gated", headers=headers).status_code == 403
    client.post("/api/v1/auth/verify-email", json={"token": token_from(outbox[0])})
    # Token predates verification; the dependency falls back to the account record
    assert gated.get("/gated", headers=headers).status_code == 200


def test_webhook_rejected_without_key_in_production(client, monkeypatch):
    monkeypatch.setattr(auth_config, "flutterflow_api_key", None)
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("JWT_SECRET_KEY", "p" * 48)
    get_settings.cache_clear()
    try:
        response = client.post("/api/v1/auth/flutterflow/webhook", json={"event_type": "user.created", "user_data": {"email": "x@example.com"}})
    finally:
        get_settings.cache_clear()
    assert response.status_code == 403
    assert run(accounts.get_user_by_email("x@example.com")) is None


async def test_auth_services_on_mongo(monkeypatch):
    """Unique email, atomic lockout counter, refresh reuse, denylist, TTL indexes against real Mongo."""
    import os
    from fastapi import FastAPI
    from api.auth import tokens
    from api.auth.audit import list_audit, record_audit
    from api.shutdown import on_shutdown
    from api.startup import on_startup
    from db import connection_db

    import uuid
    if not os.environ.get("MONGODB_URI"):
        pytest.skip("Set MONGODB_URI in the environment to an authorized MongoDB to run")
    # Throwaway database: other conftests may point MONGODB_URI at a real server
    db_name = f"f1ndr_test_auth_{uuid.uuid4().hex[:12]}"
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret")
    monkeypatch.setenv("MONGODB_DB_NAME", db_name)
    monkeypatch.setenv("MONGODB_REQUIRED", "false")
    monkeypatch.setenv("MONGODB_TIMEOUT_MS", "500")
    get_settings.cache_clear()
    app = FastAPI()
    await on_startup(app)
    database = connection_db.get_database()
    if database is None:
        get_settings.cache_clear()
        pytest.skip("MONGODB_URI not reachable or not authorized")
    try:
        assert database.name == db_name
        indexes = await database["auth_refresh_tokens"].index_information()
        assert indexes["auth_refresh_tokens_expires_at_ttl"]["expireAfterSeconds"] == 0
        assert (await database["auth_users"].index_information())["auth_users_email_unique"]["unique"]

        user = await accounts.create_user("mongo@example.com", "hash")
        with pytest.raises(accounts.UserExistsError):
            await accounts.create_user("MONGO@example.com", "hash")
        duplicate = {**user, "user_id": "other-id"}
        with pytest.raises(Exception, match="duplicate key"):
            await store.users.upsert(duplicate)

        for _ in range(auth_config.max_login_attempts - 1):
            assert await accounts.register_failed_login(user) is False
        assert await accounts.register_failed_login(user) is True
        assert accounts.lock_remaining_seconds(await accounts.get_user(user["user_id"])) > 0

        first = await tokens.issue_refresh_token(user["user_id"])
        rotated = await tokens.rotate_refresh_token(first)
        with pytest.raises(tokens.RefreshTokenReused):
            await tokens.rotate_refresh_token(first)
        with pytest.raises(tokens.RefreshTokenReused):
            await tokens.rotate_refresh_token(rotated["new_refresh_token"])

        claims = tokens.verify_token(tokens.create_access_token(user["user_id"]))
        assert await tokens.is_access_token_revoked(claims["jti"]) is False
        await tokens.revoke_access_token(claims)
        assert await tokens.is_access_token_revoked(claims["jti"]) is True

        verification = await accounts.create_email_verification_token(user)
        assert (await accounts.verify_email_token(verification))["email_verified"] is True
        assert await accounts.verify_email_token(verification) is None

        await record_audit("mongo_test", user_id=user["user_id"])
        assert (await list_audit({"user_id": user["user_id"], "event": "mongo_test"}))[0]["created_at"].endswith("Z")
    finally:
        await connection_db.get_client().drop_database(db_name)
        await on_shutdown(app)
        get_settings.cache_clear()


def test_webhook_creates_verified_passwordless_user(client, monkeypatch):
    monkeypatch.setattr(auth_config, "flutterflow_api_key", "ff-key")
    body = {"event_type": "user.created", "user_data": {"email": "FF@example.com"}}
    assert client.post("/api/v1/auth/flutterflow/webhook", json={**body, "api_key": "wrong"}).status_code == 403
    assert client.post("/api/v1/auth/flutterflow/webhook", json={**body, "api_key": "ff-key"}).status_code == 200
    user = run(accounts.get_user_by_email("ff@example.com"))
    assert user["email_verified"] is True and user["password_hash"] is None
    assert login(client, "ff@example.com").status_code == 401
