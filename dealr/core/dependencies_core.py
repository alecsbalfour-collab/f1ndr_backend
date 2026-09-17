from fastapi import Depends, HTTPException, status
from dealr.core.dealr_service_core import DealrService
from dealr.core.security_core import decode_access_token


def get_dealr_service() -> DealrService:
    """
    Dependency that returns a fresh DealrService instance.
    """
    return DealrService()


def get_current_dealr(
    token: str,
    service: DealrService = Depends(get_dealr_service)
):
    """
    Validates the dealer's JWT token and returns the dealer identity.
    """

    try:
        payload = decode_access_token(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    dealer_id = payload.get("sub")
    if not dealer_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    # Replace with real DB lookup
    return {
        "dealer_id": dealer_id,
        "role": "dealer"
    }
