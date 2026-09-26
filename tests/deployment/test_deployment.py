# f1ndr_backend/tests/deployment/test_deployment.py

import os

import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("ENVIRONMENT") is None,
    reason="Deployment checks only run when ENVIRONMENT is set",
)


def test_required_env_vars():
    required = [
        "MONGODB_URI",
        "ENVIRONMENT",
        "JWT_SECRET_KEY",
    ]

    for key in required:
        assert os.getenv(key) is not None, f"Missing environment variable: {key}"


def test_environment_is_valid():
    env = os.getenv("ENVIRONMENT")
    assert env in ["development", "test", "staging", "production"]
