from typing import List, Dict, Any
from dealr.core.vin_service_core import batch_decode_vins


class BulkVinService:
    """
    Handles bulk VIN decoding using the VinService + batch_decode_vins helper.
    This service is used by the bulk VIN upload workflow in the dealr module.
    """

    async def decode_vins(self, vins: List[str]) -> List[Dict[str, Any]]:
        """
        Decodes a list of VINs using the batch_decode_vins function.
        """

        if not vins:
            return []

        results = await batch_decode_vins(vins)
        return results

    async def decode_vins_with_job(self, job_id: str, vins: List[str]) -> Dict[str, Any]:
        """
        Simulates a job-based batch VIN decode.
        Replace this with real DB job tracking later.
        """

        decoded = await self.decode_vins(vins)

        return {
            "job_id": job_id,
            "count": len(vins),
            "results": decoded,
            "status": "completed"
        }
