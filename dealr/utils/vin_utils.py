"""dealr.utils.vin_utils — VIN normalisation and full ISO 3779 check-digit validation."""

import re
from typing import Tuple

# NHTSA transliteration table (letters → digits for check-digit calc)
_TRANSLITERATION: dict[str, int] = {
    "A": 1,  "B": 2,  "C": 3,  "D": 4,  "E": 5,  "F": 6,  "G": 7,  "H": 8,
    "J": 1,  "K": 2,  "L": 3,  "M": 4,  "N": 5,  "P": 7,  "R": 9,
    "S": 2,  "T": 3,  "U": 4,  "V": 5,  "W": 6,  "X": 7,  "Y": 8,  "Z": 9,
    "1": 1,  "2": 2,  "3": 3,  "4": 4,  "5": 5,  "6": 6,  "7": 7,  "8": 8,
    "9": 9,  "0": 0,
}

# Position weights (positions 1–17)
_WEIGHTS: list[int] = [8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2]

_VIN_RE = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$")


def normalize_vin(vin: str) -> str:
    """Strip whitespace and upper-case a VIN string."""
    return vin.strip().upper()


def validate_vin(vin: str) -> Tuple[bool, str]:
    """
    Validate a normalised 17-character VIN.

    Returns:
        (True, "")        — valid VIN
        (False, reason)   — invalid VIN with a human-readable reason
    """
    if len(vin) != 17:
        return False, f"VIN must be 17 characters, got {len(vin)}."

    if not _VIN_RE.match(vin):
        return False, "VIN contains invalid characters (I, O, Q not allowed)."

    # Check digit (position 9, 0-indexed: 8)
    total = sum(_TRANSLITERATION[ch] * _WEIGHTS[i] for i, ch in enumerate(vin))
    remainder = total % 11
    expected_check = "X" if remainder == 10 else str(remainder)

    if vin[8] != expected_check:
        return False, f"Check digit invalid: got '{vin[8]}', expected '{expected_check}'."

    return True, ""
