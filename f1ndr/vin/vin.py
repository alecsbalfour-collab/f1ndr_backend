"""
Real VIN decoding + validation for f1ndr.
Uses NHTSA vPIC API (free, unlimited).
"""

import requests
from typing import Dict, Any


VPIC_URL = "https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValuesExtended/{vin}?format=json"


def decode_vin(vin: str) -> Dict[str, Any]:
    vin = vin.strip().upper()

    if len(vin) != 17:
        return {
            "vin": vin,
            "valid": False,
            "error": "VIN must be 17 characters"
        }

    response = requests.get(VPIC_URL.format(vin=vin), timeout=10)
    response.raise_for_status()

    data = response.json().get("Results", [{}])[0]

    return {
        "vin": vin,
        "valid": True,
        "make": data.get("Make"),
        "model": data.get("Model"),
        "year": int(data.get("ModelYear")) if data.get("ModelYear") else None,
        "body_class": data.get("BodyClass"),
        "vehicle_type": data.get("VehicleType"),
        "manufacturer": data.get("Manufacturer"),
        "plant_country": data.get("PlantCountry"),
        "plant_company": data.get("PlantCompanyName"),
        "engine_cylinders": data.get("EngineCylinders"),
        "engine_displacement": data.get("DisplacementL"),
        "transmission_style": data.get("TransmissionStyle"),
        "drive_type": data.get("DriveType"),
        "fuel_type": data.get("FuelTypePrimary"),
    }
