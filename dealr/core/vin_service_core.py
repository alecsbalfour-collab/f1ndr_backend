import httpx
from typing import Dict, Any, List, Optional
from dealr.config import get_settings
from dealr.data.models_data import VinDecodeResult


def _detect_mismatches(
    result: VinDecodeResult,
    year: Optional[str],
    make: Optional[str],
    model: Optional[str],
    trim: Optional[str],
) -> List[str]:
    """Compare dealer-entered fields with decoded VIN fields (case-insensitive)."""
    flags = []
    for name, entered, decoded in (("year", year, result.year), ("make", make, result.make), ("model", model, result.model)):
        if entered is not None and decoded is not None and str(entered).strip().lower() != str(decoded).strip().lower():
            flags.append(f"{name}_mismatch")
    return flags


class VinService:
    """
    Core VIN intelligence service for decoding VINs using NHTSA vPIC API.
    """

    def __init__(self):
        self.settings = get_settings()
        self.api_url = (
            "https://vpic.nhtsa.dot.gov/api/vehicles/"
            "DecodeVinValuesExtended/{vin}?format=json"
        )

    async def decode_vin(self, vin: str) -> Dict[str, Any]:
        """
        Calls NHTSA vPIC API and returns decoded VIN data.
        """

        url = self.api_url.format(vin=vin)

        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()

        data = response.json()
        results = data.get("Results", [{}])[0]

        return {
            "vin": vin,
            "make": results.get("Make"),
            "model": results.get("Model"),
            "year": results.get("ModelYear"),
            "body_class": results.get("BodyClass"),
            "engine": results.get("EngineModel"),
            "manufacturer": results.get("Manufacturer"),
            "plant_country": results.get("PlantCountry"),
            "plant_company": results.get("PlantCompanyName"),
            "raw": results
        }


async def batch_decode_vins(vins: List[str]) -> List[Dict[str, Any]]:
    """
    Batch VIN decoding using VinService.
    """

    service = VinService()
    results = []

    for vin in vins:
        decoded = await service.decode_vin(vin)
        results.append(decoded)

    return results
