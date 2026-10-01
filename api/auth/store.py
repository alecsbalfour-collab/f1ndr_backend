# api/auth/store.py
"""Collections used by the auth services."""

from datetime import datetime, timezone

from db.document_store import DocumentStore

users = DocumentStore("auth_users", key="user_id", unique=("email",))
# One doc per issued refresh token; kept (revoked) until expiry so reuse can be detected
refresh_tokens = DocumentStore("auth_refresh_tokens", key="jti", indexes=("user_id",), ttl_field="expires_at")
# Denylist of access-token jtis revoked before their natural expiry
revoked_access_tokens = DocumentStore("auth_revoked_tokens", key="jti", ttl_field="expires_at")
email_tokens = DocumentStore("auth_email_tokens", key="token_hash", indexes=("user_id",), ttl_field="expires_at")
audit_log = DocumentStore("audit_log", key="id", indexes=("user_id", "event", "created_at"))


def utcnow() -> datetime:
    """Naive UTC, which is what Mongo stores and returns (and what TTL indexes expect)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def clear_memory() -> None:
    for store in (users, refresh_tokens, revoked_access_tokens, email_tokens, audit_log):
        store.clear_memory()
