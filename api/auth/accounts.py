# api/auth/accounts.py
"""User accounts: creation, lockout, email verification, roles."""

import hashlib
import secrets
import uuid
from datetime import timedelta
from typing import Any, Dict, List, Optional

from pymongo.errors import DuplicateKeyError

from api.auth import store
from api.auth.roles import DEFAULT_ROLES, validate_roles
from api.config.settings_config import get_settings
from f1ndr.config.auth_config import auth_config


class UserExistsError(Exception):
    pass


def normalize_email(email: str) -> str:
    return email.strip().lower()


def _iso(value) -> Optional[str]:
    return value.isoformat() + "Z" if value is not None else None


def public_user(user: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "user_id": user["user_id"],
        "email": user["email"],
        "name": user.get("name", ""),
        "email_verified": bool(user.get("email_verified")),
        "roles": user.get("roles", []),
        "created_at": _iso(user.get("created_at")),
    }


async def get_user(user_id: str) -> Optional[dict]:
    return await store.users.get(user_id)


async def get_user_by_email(email: str) -> Optional[dict]:
    found = await store.users.find({"email": normalize_email(email)}, limit=1)
    return found[0] if found else None


async def create_user(email: str, password_hash: Optional[str], name: str = "", email_verified: bool = False) -> dict:
    email = normalize_email(email)
    if await get_user_by_email(email):
        raise UserExistsError(email)
    user = {
        "user_id": str(uuid.uuid4()),
        "email": email,
        "password_hash": password_hash,
        "name": name,
        "roles": list(DEFAULT_ROLES),
        "email_verified": email_verified,
        "email_verified_at": store.utcnow() if email_verified else None,
        "failed_login_count": 0,
        "locked_until": None,
        "created_at": store.utcnow(),
    }
    try:
        await store.users.upsert(user)
    except DuplicateKeyError:
        raise UserExistsError(email)
    return user


def lock_remaining_seconds(user: dict) -> int:
    locked_until = user.get("locked_until")
    if locked_until is None:
        return 0
    return max(0, int((locked_until - store.utcnow()).total_seconds()))


async def register_failed_login(user: dict) -> bool:
    """Count a failed password attempt; returns True if this attempt locked the account."""
    failures = await store.users.increment(user["user_id"], "failed_login_count")
    if failures is None or failures < auth_config.max_login_attempts:
        return False
    until = store.utcnow() + timedelta(minutes=auth_config.lockout_duration_minutes)
    await store.users.update(user["user_id"], {"locked_until": until, "failed_login_count": 0})
    return True


async def clear_lockout(user_id: str) -> bool:
    return await store.users.update(user_id, {"failed_login_count": 0, "locked_until": None})


async def record_login(user_id: str) -> None:
    await store.users.update(user_id, {"failed_login_count": 0, "locked_until": None, "last_login_at": store.utcnow()})


async def set_roles(user_id: str, roles: List[str]) -> Optional[dict]:
    roles = validate_roles(roles)
    if not await store.users.update(user_id, {"roles": roles}):
        return None
    return await get_user(user_id)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


async def create_email_verification_token(user: dict) -> str:
    """Issue a single-use token (only its hash is stored); older tokens for the user are dropped."""
    for old in await store.email_tokens.find({"user_id": user["user_id"]}, limit=100):
        await store.email_tokens.delete(old["token_hash"])
    token = secrets.token_urlsafe(32)
    await store.email_tokens.upsert({
        "token_hash": _hash_token(token),
        "user_id": user["user_id"],
        "email": user["email"],
        "purpose": "verify_email",
        "created_at": store.utcnow(),
        "expires_at": store.utcnow() + timedelta(hours=auth_config.email_verification_expiry_hours),
    })
    return token


async def verify_email_token(token: str) -> Optional[dict]:
    """Consume a verification token; returns the updated user, or None if invalid/expired."""
    token_hash = _hash_token(token)
    record = await store.email_tokens.get(token_hash)
    if record is None or not await store.email_tokens.delete(token_hash):
        return None
    user = await get_user(record["user_id"])
    if record["expires_at"] < store.utcnow() or user is None or user["email"] != record["email"]:
        return None
    roles = user.get("roles", [])
    if user["email"] in get_settings().admin_emails and "admin" not in roles:
        roles = roles + ["admin"]
    await store.users.update(user["user_id"], {"email_verified": True, "email_verified_at": store.utcnow(), "roles": roles})
    return await get_user(user["user_id"])
