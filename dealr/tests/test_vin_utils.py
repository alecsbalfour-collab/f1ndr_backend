"""Tests for dealr.utils.vin_utils — normalisation and check-digit validation."""

import pytest

from dealr.utils.vin_utils import normalize_vin, validate_vin


class TestNormalizeVin:
    def test_upper_cases(self) -> None:
        assert normalize_vin("1hgcm82633a004352") == "1HGCM82633A004352"

    def test_strips_whitespace(self) -> None:
        assert normalize_vin("  1HGCM82633A004352  ") == "1HGCM82633A004352"

    def test_already_normalised(self) -> None:
        assert normalize_vin("1HGCM82633A004352") == "1HGCM82633A004352"


class TestValidateVin:
    VALID = "1HGCM82633A004352"

    def test_valid_vin(self) -> None:
        ok, reason = validate_vin(self.VALID)
        assert ok is True
        assert reason == ""

    def test_too_short(self) -> None:
        ok, reason = validate_vin("1HGCM826")
        assert ok is False
        assert "17 characters" in reason

    def test_invalid_char_i(self) -> None:
        ok, reason = validate_vin("1HGCM82633A00435I")
        assert ok is False
        assert "invalid characters" in reason

    def test_invalid_char_o(self) -> None:
        ok, reason = validate_vin("1HGCM82633A00435O")
        assert ok is False

    def test_bad_check_digit(self) -> None:
        bad = list(self.VALID)
        bad[8] = "0" if bad[8] != "0" else "1"
        ok, reason = validate_vin("".join(bad))
        assert ok is False
        assert "Check digit" in reason

    def test_real_world_vins(self) -> None:
        known_valid = [
            "1HGCM82633A004352",  # Honda Accord
            "JH4KA8271NC000001",  # Acura
            "WBAJB0C51BC613639",  # BMW
        ]
        for vin in known_valid:
            ok, _ = validate_vin(vin)
            assert ok is True, f"Expected valid VIN: {vin}"
