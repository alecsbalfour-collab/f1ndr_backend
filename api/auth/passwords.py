# api/auth/passwords.py

from typing import List, Optional, Tuple

import bcrypt

from f1ndr.config.auth_config import auth_config

BCRYPT_MAX_BYTES = 72
SPECIAL_CHARACTERS = "!@#$%^&*()_+-=[]{}|;:,.<>?"
# Compared against when the account doesn't exist, so response time doesn't reveal it
_DUMMY_HASH = bcrypt.hashpw(b"dummy-password", bcrypt.gensalt()).decode()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: Optional[str]) -> bool:
    try:
        matches = bcrypt.checkpw(password.encode("utf-8"), (hashed or _DUMMY_HASH).encode())
    except ValueError:
        return False
    return matches and hashed is not None


def validate_password_strength(password: str) -> Tuple[bool, List[str]]:
    errors = []
    if len(password) < auth_config.password_min_length:
        errors.append(f"Password must be at least {auth_config.password_min_length} characters")
    if len(password.encode("utf-8")) > BCRYPT_MAX_BYTES:
        errors.append(f"Password must be at most {BCRYPT_MAX_BYTES} bytes")
    if auth_config.password_require_uppercase and not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")
    if auth_config.password_require_lowercase and not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")
    if auth_config.password_require_numbers and not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one number")
    if auth_config.password_require_special and not any(c in SPECIAL_CHARACTERS for c in password):
        errors.append("Password must contain at least one special character")
    return len(errors) == 0, errors
