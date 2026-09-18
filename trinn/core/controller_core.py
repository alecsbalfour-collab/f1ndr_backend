# f1ndr-backend/trinn/core/controller_core.py
"""
DICT-aligned TRINN controller layer with enterprise features.
"""

import logging
from typing import Dict, Any

from trinn.core.service_core import TrinnService
from trinn.core.exceptions_core import TrinnError


logger = logging.getLogger(__name__)


class TrinnController:
    """Enterprise TRINN controller with DICT patterns."""
    
    def __init__(self, service: TrinnService):
        self.service = service
        logger.info("TrinnController initialized")
    
    async def run_pipeline(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute pipeline with enterprise-level orchestration.
        
        Args:
            payload: Input data for pipeline processing
            
        Returns:
            Dictionary with pipeline results and metadata
        """
        try:
            logger.info(f"Controller received pipeline request: {payload.get('task', 'unknown')}")
            
            # Execute pipeline through service layer
            result = await self.service.run_pipeline(payload)
            
            # Add controller-level metadata
            result["controller_metadata"] = {
                "status": "completed",
                "feature_key": "trinn_controller",
                "timestamp": self._get_timestamp(),
            }
            
            logger.info("Controller pipeline execution completed successfully")
            return result
            
        except TrinnError as e:
            logger.error(f"Controller pipeline execution failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in controller: {e}")
            raise TrinnError(f"Controller error: {str(e)}")
    
    async def get_service_metrics(self) -> Dict[str, Any]:
        """Get service metrics for monitoring."""
        return self.service.get_metrics()
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.utcnow().isoformat()
