import pytest


@pytest.fixture(autouse=True)
def reset_rate_limits():
    """All TestClient requests share one client IP; keep rate-limit windows per test."""
    from api.security.rate_limiter import limiter
    limiter.reset()
    yield


@pytest.fixture(scope="session")
def headers_for():
    """`headers_for("dealer", sub="d1")` -> Authorization header for an access token with that role's scopes."""
    from api.auth.roles import scopes_for_roles
    from api.routes.auth_routes import create_access_token

    def make(role: str = "user", sub: str = None):
        claims = {"roles": [role], "scopes": scopes_for_roles([role])}
        return {"Authorization": f"Bearer {create_access_token(sub or f'{role}-user', claims)}"}
    return make
