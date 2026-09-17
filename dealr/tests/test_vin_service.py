"""Tests for dealr.core.vin_service_core — mismatch detection and cache behaviour."""

import pytest

from dealr.core.vin_service_core import _detect_mismatches
from dealr.data.models_data import DecodeStatus, VinDecodeResult


def _make_result(**kwargs) -> VinDecodeResult:
    defaults = dict(
        vin="1HGCM82633A004352",
        year="2003",
        make="Honda",
        model="Accord",
        trim="EX",
        decode_status=DecodeStatus.success,
    )
    defaults.update(kwargs)
    return VinDecodeResult(**defaults)


class TestDetectMismatches:
    def test_no_mismatches_when_identical(self) -> None:
        result = _make_result()
        flags = _detect_mismatches(result, "2003", "Honda", "Accord", "EX")
        assert flags == []

    def test_case_insensitive_comparison(self) -> None:
        result = _make_result(make="honda")
        flags = _detect_mismatches(result, "2003", "HONDA", "Accord", "EX")
        assert "make_mismatch" not in flags

    def test_year_mismatch_detected(self) -> None:
        result = _make_result(year="2003")
        flags = _detect_mismatches(result, "2005", "Honda", "Accord", "EX")
        assert "year_mismatch" in flags

    def test_make_mismatch_detected(self) -> None:
        result = _make_result(make="Honda")
        flags = _detect_mismatches(result, "2003", "Toyota", "Accord", "EX")
        assert "make_mismatch" in flags

    def test_model_mismatch_detected(self) -> None:
        result = _make_result(model="Accord")
        flags = _detect_mismatches(result, "2003", "Honda", "Civic", "EX")
        assert "model_mismatch" in flags

    def test_none_dealer_fields_skip_check(self) -> None:
        result = _make_result()
        flags = _detect_mismatches(result, None, None, None, None)
        assert flags == []

    def test_multiple_mismatches(self) -> None:
        result = _make_result(year="2003", make="Honda")
        flags = _detect_mismatches(result, "2010", "Toyota", "Accord", "EX")
        assert "year_mismatch" in flags
        assert "make_mismatch" in flags
