# f1ndr-backend/trinn/module.py
"""
DICT-aligned TRINN module entrypoint with enterprise features.
"""

import logging
from typing import Dict, Any

from trinn.core.core import run_task, schedule_task
from trinn.config.config import get_trinn_config


logger = logging.getLogger(__name__)


class TrinnModule:
    """Enterprise TRINN module with DICT patterns."""
    
    def __init__(self):
        self.config = get_trinn_config()
        logger.info(f"TrinnModule initialized: {self.config['feature_key']}")
    
    async def run(self, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute TRINN module action with enterprise orchestration.
        
        Args:
            action: Action type ('run' or 'schedule')
            data: Action data
            
        Returns:
            Dictionary with action results and metadata
        """
        try:
            logger.info(f"Executing TRINN module action: {action}")
            
            if action == "run":
                result = await run_task(data)
            elif action == "schedule":
                result = await schedule_task(data)
            else:
                raise ValueError(f"Invalid trinn action: {action}")
            
            # Add module-level metadata
            result["module_metadata"] = {
                "feature_key": self.config["feature_key"],
                "feature_version": self.config["feature_version"],
                "action": action,
                "timestamp": self._get_timestamp(),
            }
            
            logger.info(f"TRINN module action completed: {action}")
            return result
            
        except Exception as e:
            logger.error(f"TRINN module action failed: {e}")
            raise
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.utcnow().isoformat()


_module: TrinnModule | None = None


async def run(action: str, data: Dict[str, Any]) -> Dict[str, Any]:
    global _module
    if _module is None:
        _module = TrinnModule()
    return await _module.run(action, data)
