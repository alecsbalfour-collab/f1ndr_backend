"""
Real VIN decoding for f1ndr.
Uses NHTSA vPIC API (free, unlimited).
Fully functional, no placeholders.
"""

import requests
from typing import Dict, Any


VPIC_URL = (
    "https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValuesExtended/{vin}?format=json"
)


def decode_vin(vin: str) -> Dict[str, Any]:
    """
    Fully functional VIN decode using NHTSA vPIC.
    Returns structured vehicle metadata.
    """

    vin = vin.strip().upper()

    # Basic validation
    if len(vin) != 17:
        return {
            "vin": vin,
            "valid": False,
            "error": "VIN must be exactly 17 characters",
        }

    try:
        response = requests.get(VPIC_URL.format(vin=vin), timeout=10)
        response.raise_for_status()
    except Exception as e:
        return {
            "vin": vin,
            "valid": False,
            "error": f"VIN decode request failed: {str(e)}",
        }

    data = response.json().get("Results", [{}])[0]

    decoded = {
        "vin": vin,
        "valid": True,
        "make": data.get("Make"),
        "model": data.get("Model"),
        "year": _safe_int(data.get("ModelYear")),
        "manufacturer": data.get("Manufacturer"),
        "vehicle_type": data.get("VehicleType"),
        "body_class": data.get("BodyClass"),
        "drive_type": data.get("DriveType"),
        "fuel_type": data.get("FuelTypePrimary"),
        "engine_cylinders": _safe_int(data.get("EngineCylinders")),
        "engine_displacement_l": _safe_float(data.get("DisplacementL")),
        "transmission_style": data.get("TransmissionStyle"),
        "plant_country": data.get("PlantCountry"),
        "plant_company": data.get("PlantCompanyName"),
        "series": data.get("Series"),
        "trim": data.get("Trim"),
        "doors": _safe_int(data.get("Doors")),
        "gvwr": data.get("GVWR"),
        "error_text": data.get("ErrorText"),
    }

    return decoded


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except:
        return None


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except:
        return None
