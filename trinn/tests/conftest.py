"""Local fixtures for trinn tests (mirrors tests/conftest.py's headers_for)."""

import pytest


@pytest.fixture()
def headers_for():
    """`headers_for("dealer", sub="d1")` -> Authorization header for a token with that role's scopes."""
    from api.auth.roles import scopes_for_roles
    from api.auth.tokens import create_access_token

    def make(role: str = "user", sub: str = None):
        claims = {"roles": [role], "scopes": scopes_for_roles([role])}
        return {"Authorization": f"Bearer {create_access_token(sub or f'{role}-user', claims)}"}

    return make
