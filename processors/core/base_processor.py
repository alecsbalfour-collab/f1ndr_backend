# f1ndr-backend/processors/core/base_processor.py
"""
DICT-aligned base processor with enterprise features and FlutterFlow compatibility.
"""

import logging
from typing import Dict, Any
from datetime import datetime


logger = logging.getLogger(__name__)


class BaseProcessor:
    """Enterprise base processor with DICT patterns and FlutterFlow compatibility."""
    
    def __init__(self, base_config, logger, validator, exceptions, formatter):
        self.base_config = base_config
        self.logger = logger
        self.validator = validator
        self.exceptions = exceptions
        self.formatter = formatter
        logger.info("BaseProcessor initialized with enterprise features")

    def process(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process payload with enterprise validation and FlutterFlow-compatible response.
        
        Args:
            payload: Input data to process
            
        Returns:
            Dictionary with processing results and metadata
        """
        try:
            if not self.base_config.defaults().get("enabled", True):
                self.logger.warning("Base processor disabled")
                return {
                    "status": "disabled",
                    "success": False,
                    "message": "Processor is disabled",
                    "timestamp": datetime.utcnow().isoformat(),
                }

            errors = self.validator.validate(payload)
            if errors:
                self.logger.error(f"Validation errors: {errors}")
                raise self.exceptions.ValidationException(str(errors))

            formatted = self.formatter.format_payload(payload)
            self.logger.info("Base processor completed successfully")
            
            return {
                "status": "ok",
                "success": True,
                "payload": formatted,
                "timestamp": datetime.utcnow().isoformat(),
                "processor": "base",
            }
            
        except Exception as e:
            logger.error(f"Base processor failed: {e}")
            return {
                "status": "error",
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "processor": "base",
            }
