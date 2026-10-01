from typing import Any, Callable, Dict

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from api.auth.accounts import get_user
from api.auth.tokens import is_access_token_revoked, verify_token

bearer = HTTPBearer(auto_error=False)
_BEARER = {"WWW-Authenticate": "Bearer"}


async def require_user(credentials: HTTPAuthorizationCredentials = Depends(bearer)) -> Dict[str, Any]:
    """Reject requests without a valid, unrevoked access token; return its claims."""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated", headers=_BEARER)
    claims = verify_token(credentials.credentials)
    if claims.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type", headers=_BEARER)
    if await is_access_token_revoked(claims.get("jti")):
        raise HTTPException(status_code=401, detail="Token has been revoked", headers=_BEARER)
    return claims


def is_admin(claims: Dict[str, Any]) -> bool:
    return "users:admin" in (claims.get("scopes") or [])


def owns(claims: Dict[str, Any], document: Dict[str, Any], owner_field: str) -> bool:
    """The caller owns `document`, or is an admin. Documents without an owner are admin-only."""
    return is_admin(claims) or (document.get(owner_field) is not None and document.get(owner_field) == claims["sub"])


def require_scopes(*scopes: str) -> Callable:
    """Dependency factory: the access token must carry every listed scope."""
    async def dependency(claims: Dict[str, Any] = Depends(require_user)) -> Dict[str, Any]:
        missing = set(scopes) - set(claims.get("scopes") or [])
        if missing:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return claims
    return dependency


async def require_verified_email(claims: Dict[str, Any] = Depends(require_user)) -> Dict[str, Any]:
    # Tokens issued before verification carry email_verified=False, so confirm against the account
    if not claims.get("email_verified"):
        user = await get_user(claims["sub"])
        if not (user and user.get("email_verified")):
            raise HTTPException(status_code=403, detail="Email address not verified")
    return claims
