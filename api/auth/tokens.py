# api/auth/tokens.py
"""
JWT issuing and revocation.

Refresh tokens are persisted by `jti` and rotated on every use; presenting an
already-used refresh token revokes its whole family (the login session), since
that means it was stolen or replayed. Access tokens are short-lived and checked
against a jti denylist populated on logout.
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import HTTPException
from jose import JWTError, jwt

from api.auth import store
from api.auth.roles import scopes_for_roles
from api.config.settings_config import get_settings
from f1ndr.config.auth_config import auth_config

logger = logging.getLogger(__name__)

_BEARER = {"WWW-Authenticate": "Bearer"}


class RefreshTokenReused(HTTPException):
    def __init__(self, user_id: str, family: str):
        super().__init__(status_code=401, detail="Refresh token has been revoked", headers=_BEARER)
        self.user_id = user_id
        self.family = family


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(status_code=401, detail=detail, headers=_BEARER)


def _encode(claims: Dict[str, Any], lifetime: timedelta) -> str:
    now = datetime.now(timezone.utc)
    claims = {"iat": int(now.timestamp()), "exp": int((now + lifetime).timestamp()), **claims}
    claims.setdefault("jti", str(uuid.uuid4()))
    settings = get_settings()
    return jwt.encode(claims, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def access_claims_for(user: Dict[str, Any]) -> Dict[str, Any]:
    roles = user.get("roles", [])
    return {
        "email": user["email"],
        "name": user.get("name", ""),
        "roles": roles,
        "scopes": scopes_for_roles(roles),
        "email_verified": bool(user.get("email_verified")),
    }


def create_access_token(user_id: str, additional_claims: Optional[Dict[str, Any]] = None) -> str:
    claims = {"sub": user_id, "type": "access"}
    if auth_config.flutterflow_app_id:
        claims["app_id"] = auth_config.flutterflow_app_id
    claims.update(additional_claims or {})
    return _encode(claims, timedelta(minutes=auth_config.token_expiry_minutes))


def create_refresh_token(user_id: str, jti: Optional[str] = None, family: Optional[str] = None) -> str:
    jti = jti or str(uuid.uuid4())
    claims = {"sub": user_id, "type": "refresh", "jti": jti, "fam": family or jti}
    return _encode(claims, timedelta(days=auth_config.refresh_token_expiry_days))


def verify_token(token: str) -> Dict[str, Any]:
    try:
        settings = get_settings()
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError as e:
        logger.info("Token verification failed: %s", e)
        raise _unauthorized("Invalid token")


def _expiry(claims: Dict[str, Any]) -> datetime:
    return datetime.fromtimestamp(claims["exp"], timezone.utc).replace(tzinfo=None)


async def issue_refresh_token(user_id: str, family: Optional[str] = None) -> str:
    """Create and persist a refresh token. A new family (login) evicts the oldest sessions over the limit."""
    jti = str(uuid.uuid4())
    token = create_refresh_token(user_id, jti=jti, family=family)
    now = store.utcnow()
    await store.refresh_tokens.upsert({
        "jti": jti,
        "user_id": user_id,
        "family": family or jti,
        "created_at": now,
        "expires_at": _expiry(verify_token(token)),
        "use_count": 0,
        "revoked_at": None,
        "revoked_reason": None,
    })
    if family is None:
        await _enforce_session_limit(user_id)
    return token


async def _active_refresh_tokens(user_id: str, **query) -> list:
    now = store.utcnow()
    docs = await store.refresh_tokens.find({"user_id": user_id, "revoked_at": None, **query}, limit=1000)
    return [d for d in docs if d["expires_at"] > now]


async def _revoke(docs: list, reason: str) -> int:
    now = store.utcnow()
    for doc in docs:
        await store.refresh_tokens.update(doc["jti"], {"revoked_at": now, "revoked_reason": reason})
    return len(docs)


async def _enforce_session_limit(user_id: str) -> None:
    limit = auth_config.max_sessions_per_user
    if limit <= 0:
        return
    active = sorted(await _active_refresh_tokens(user_id), key=lambda d: d["created_at"])
    await _revoke(active[:-limit] if len(active) > limit else [], "session_limit")


async def rotate_refresh_token(token: str) -> Dict[str, Any]:
    """Consume a refresh token and return its claims plus a `new_refresh_token` in the same family."""
    claims = verify_token(token)
    if claims.get("type") != "refresh":
        raise _unauthorized("Invalid token type")
    record = await store.refresh_tokens.get(claims.get("jti"))
    if record is None or record["user_id"] != claims.get("sub"):
        raise _unauthorized("Invalid token")
    # Atomic claim: only the first presenter of a refresh token may use it
    uses = await store.refresh_tokens.increment(record["jti"], "use_count")
    if record["revoked_at"] is not None or uses != 1:
        await revoke_family(record["family"], "reuse_detected")
        raise RefreshTokenReused(record["user_id"], record["family"])
    await _revoke([record], "rotated")
    return {**claims, "new_refresh_token": await issue_refresh_token(record["user_id"], family=record["family"])}


async def revoke_family(family: str, reason: str) -> int:
    docs = await store.refresh_tokens.find({"family": family, "revoked_at": None}, limit=1000)
    return await _revoke(docs, reason)


async def revoke_refresh_token(token: str, user_id: str, reason: str = "logout") -> bool:
    """Revoke the session a refresh token belongs to, if it belongs to `user_id`."""
    try:
        claims = verify_token(token)
    except HTTPException:
        return False
    if claims.get("type") != "refresh" or claims.get("sub") != user_id:
        return False
    return await revoke_family(claims.get("fam") or claims["jti"], reason) > 0


async def revoke_all_refresh_tokens(user_id: str, reason: str) -> int:
    return await _revoke(await _active_refresh_tokens(user_id), reason)


async def revoke_access_token(claims: Dict[str, Any]) -> None:
    await store.revoked_access_tokens.upsert({
        "jti": claims["jti"],
        "user_id": claims.get("sub"),
        "revoked_at": store.utcnow(),
        "expires_at": _expiry(claims),
    })


async def is_access_token_revoked(jti: Optional[str]) -> bool:
    return jti is None or await store.revoked_access_tokens.get(jti) is not None
