from typing import Any, Dict

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from api.routes.auth_routes import verify_token

bearer = HTTPBearer(auto_error=False)


async def require_user(credentials: HTTPAuthorizationCredentials = Depends(bearer)) -> Dict[str, Any]:
    """Reject requests without a valid access token; return its claims."""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated", headers={"WWW-Authenticate": "Bearer"})
    claims = verify_token(credentials.credentials)
    if claims.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type", headers={"WWW-Authenticate": "Bearer"})
    return claims
