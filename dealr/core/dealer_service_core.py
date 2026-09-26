"""dealr.core.dealer_service_core — Mongo-backed dealer authentication."""

from typing import Tuple

from dealr.core.errors_core import AuthError
from dealr.core.security_core import create_access_token, verify_password
from dealr.db.collections_db import get_dealers_collection


async def authenticate_dealer(email: str, password: str) -> Tuple[str, str]:
    """Return (access_token, dealer_id) or raise AuthError."""
    doc = await get_dealers_collection().find_one({"email": email.strip().lower()})
    if not doc or not verify_password(password, doc["password_hash"]):
        raise AuthError("Invalid email or password.")
    dealer_id = doc["dealer_id"]
    return create_access_token(dealer_id), dealer_id
