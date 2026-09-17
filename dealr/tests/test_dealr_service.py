"""Tests for dealr.core.dealer_service_core — password hashing and auth logic."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from dealr.core.security_core import hash_password, verify_password


class TestPasswordHashing:
    def test_hash_is_not_plain_text(self) -> None:
        hashed = hash_password("secret123")
        assert hashed != "secret123"

    def test_verify_correct_password(self) -> None:
        hashed = hash_password("correct-horse-battery-staple")
        assert verify_password("correct-horse-battery-staple", hashed) is True

    def test_verify_wrong_password(self) -> None:
        hashed = hash_password("correct-horse-battery-staple")
        assert verify_password("wrong-password", hashed) is False

    def test_different_hashes_same_password(self) -> None:
        h1 = hash_password("same-password")
        h2 = hash_password("same-password")
        # bcrypt generates unique salts — hashes must differ
        assert h1 != h2


class TestAuthenticateDealer:
    @pytest.mark.anyio
    async def test_authenticate_success(self) -> None:
        from dealr.core.dealer_service_core import authenticate_dealer

        hashed = hash_password("testpass")
        fake_doc = {
            "dealer_id": "dealer-uuid-001",
            "email": "test@dealr.ca",
            "password_hash": hashed,
        }
        mock_col = AsyncMock()
        mock_col.find_one = AsyncMock(return_value=fake_doc)

        with patch("dealr.core.dealer_service_core.get_dealers_collection", return_value=mock_col):
            token, dealer_id = await authenticate_dealer("test@dealr.ca", "testpass")
            assert dealer_id == "dealer-uuid-001"
            assert isinstance(token, str) and len(token) > 0

    @pytest.mark.anyio
    async def test_authenticate_wrong_password(self) -> None:
        from dealr.core.dealer_service_core import authenticate_dealer
        from dealr.core.errors_core import AuthError

        hashed = hash_password("correct-pass")
        fake_doc = {
            "dealer_id": "dealer-uuid-001",
            "email": "test@dealr.ca",
            "password_hash": hashed,
        }
        mock_col = AsyncMock()
        mock_col.find_one = AsyncMock(return_value=fake_doc)

        with patch("dealr.core.dealer_service_core.get_dealers_collection", return_value=mock_col):
            with pytest.raises(AuthError):
                await authenticate_dealer("test@dealr.ca", "wrong-pass")

    @pytest.mark.anyio
    async def test_authenticate_nonexistent_email(self) -> None:
        from dealr.core.dealer_service_core import authenticate_dealer
        from dealr.core.errors_core import AuthError

        mock_col = AsyncMock()
        mock_col.find_one = AsyncMock(return_value=None)

        with patch("dealr.core.dealer_service_core.get_dealers_collection", return_value=mock_col):
            with pytest.raises(AuthError):
                await authenticate_dealer("nobody@dealr.ca", "any-pass")
