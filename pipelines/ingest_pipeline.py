# f1ndr-backend/pipelines/ingest_pipeline.py
"""
DICT-aligned ingest pipeline with enterprise features and FlutterFlow compatibility.
"""

import logging
from typing import Dict, Any
from datetime import datetime

from .core.pipeline_core import PipelineCore
from .utils.pipeline_logger_utils import pipeline_logger_utils
from .config.pipeline_config import pipeline_config
from .data.pipeline_data import PIPELINE_DATA
from .db.pipeline_state import pipeline_state


logger = logging.getLogger(__name__)


class ingestPipeline:
    """Enterprise ingest pipeline with DICT patterns and FlutterFlow compatibility."""
    
    def __init__(self):
        self.core = PipelineCore(
            config=pipeline_config,
            data=PIPELINE_DATA,
            state=pipeline_state,
            logger=pipeline_logger_utils.logger,
        )
        logger.info("Ingest pipeline initialized with enterprise features")

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run ingest pipeline with enterprise error handling and FlutterFlow-compatible response.
        
        Args:
            payload: Input data for pipeline processing
            
        Returns:
            Dictionary with pipeline results and metadata
        """
        try:
            pipeline_logger_utils.logger.info("Starting ingest pipeline")
            
            result = self.core.process(payload)
            
            # Add enterprise metadata
            result["metadata"] = {
                "pipeline_type": "ingest",
                "timestamp": datetime.utcnow().isoformat(),
                "feature_key": "pipelines_ingest",
                "success": True,
            }
            
            logger.info("Ingest pipeline completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Ingest pipeline failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "metadata": {
                    "pipeline_type": "ingest",
                    "timestamp": datetime.utcnow().isoformat(),
                    "feature_key": "pipelines_ingest",
                    "error_type": type(e).__name__,
                }
            }
