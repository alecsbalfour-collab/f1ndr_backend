# api/auth/roles.py
"""Roles are stored on the user; access tokens carry the scopes they expand to."""

from typing import Iterable, List

_USER_SCOPES = ["profile:read", "profile:write", "search:read", "listings:read", "listings:write"]
_DEALER_SCOPES = _USER_SCOPES + ["inventory:read", "inventory:write"]
_ADMIN_SCOPES = _DEALER_SCOPES + ["users:read", "users:admin", "audit:read", "tasks:admin"]

ROLE_SCOPES = {
    "user": _USER_SCOPES,
    "dealer": _DEALER_SCOPES,
    "admin": _ADMIN_SCOPES,
}
DEFAULT_ROLES = ["user"]


def validate_roles(roles: Iterable[str]) -> List[str]:
    """Return roles deduplicated in a stable order; raises ValueError on unknown roles."""
    roles = list(dict.fromkeys(roles))
    unknown = [r for r in roles if r not in ROLE_SCOPES]
    if unknown:
        raise ValueError(f"Unknown roles: {', '.join(unknown)}")
    return roles


def scopes_for_roles(roles: Iterable[str]) -> List[str]:
    return sorted({scope for role in roles for scope in ROLE_SCOPES.get(role, [])})
