# f1ndr-backend/trinn/core/service_core.py
"""
DICT-aligned TRINN service layer with enterprise features.
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from dataclasses import dataclass

from trinn.config.config import get_trinn_config
from trinn.config.pipeline_config import get_pipeline_config
from trinn.config.enrich_config import get_enrich_config
from trinn.config.normalize_config import get_normalize_config
from trinn.config.transform_config import get_transform_config
from trinn.core.exceptions_core import TrinnError, ValidationError
from trinn.core.validation_core import require_fields


logger = logging.getLogger(__name__)


@dataclass
class ServiceMetrics:
    """Enterprise service metrics for monitoring."""
    tasks_processed: int = 0
    tasks_failed: int = 0
    pipelines_completed: int = 0
    pipelines_failed: int = 0
    average_processing_time_ms: float = 0.0


class TrinnService:
    """Enterprise TRINN service with DICT patterns."""
    
    def __init__(self, enrich_repo, normalize_repo, transform_repo, task_repo):
        self.config = get_trinn_config()
        self.pipeline_config = get_pipeline_config()
        self.enrich_config = get_enrich_config()
        self.normalize_config = get_normalize_config()
        self.transform_config = get_transform_config()
        
        self.enrich_repo = enrich_repo
        self.normalize_repo = normalize_repo
        self.transform_repo = transform_repo
        self.task_repo = task_repo
        
        self.metrics = ServiceMetrics()
        logger.info(f"TrinnService initialized with config: {self.config['feature_key']}")
    
    async def run_pipeline(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the full TRINN pipeline with enterprise error handling.
        
        Args:
            payload: Input data for pipeline processing
            
        Returns:
            Dictionary with results from each pipeline stage
        """
        import time
        start_time = time.time()
        
        try:
            logger.info(f"Starting TRINN pipeline for payload: {payload.get('task', 'unknown')}")
            
            # Validate input
            if self.pipeline_config.validate_inputs:
                if not require_fields(payload, ["task"]):
                    raise ValidationError("Missing required field: task")
            
            # Execute pipeline stages
            result = {}
            current_data = payload
            
            for stage in self.pipeline_config.stages:
                try:
                    logger.info(f"Executing pipeline stage: {stage}")
                    stage_result = await self._execute_stage(stage, current_data)
                    result[stage] = stage_result
                    current_data = stage_result
                    
                except Exception as stage_error:
                    logger.error(f"Stage {stage} failed: {stage_error}")
                    if not self.pipeline_config.continue_on_error:
                        raise
                    result[stage] = {"error": str(stage_error), "stage": stage}
            
            # Update metrics
            processing_time = (time.time() - start_time) * 1000
            self.metrics.pipelines_completed += 1
            self.metrics.tasks_processed += 1
            self._update_average_time(processing_time)
            
            logger.info(f"Pipeline completed in {processing_time:.2f}ms")
            return result
            
        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            self.metrics.pipelines_failed += 1
            self.metrics.tasks_failed += 1
            raise TrinnError(f"Pipeline execution failed: {str(e)}")
    
    async def _execute_stage(self, stage: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single pipeline stage with enterprise error handling."""
        if stage == "enrich":
            return await self._enrich_stage(data)
        elif stage == "normalize":
            return await self._normalize_stage(data)
        elif stage == "transform":
            return await self._transform_stage(data)
        else:
            raise ValueError(f"Unknown pipeline stage: {stage}")
    
    async def _enrich_stage(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute enrich stage with enterprise processing."""
        if not self.enrich_config.enabled:
            logger.debug("Enrich stage disabled, skipping")
            return data
        
        from trinn.data.enrich_data import build_enrich_payload
        
        enriched = build_enrich_payload(data)
        
        # Validate source if required
        if self.enrich_config.enrich_source_validation:
            source = enriched.get("source")
            if not source and not self.enrich_config.continue_on_missing_source:
                raise ValidationError("Missing required source field")
        
        # Store in repository
        await self.enrich_repo.insert(enriched)
        
        logger.debug(f"Enrich stage completed for data: {data.get('id', 'unknown')}")
        return enriched
    
    async def _normalize_stage(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute normalize stage with enterprise processing."""
        if not self.normalize_config.enabled:
            logger.debug("Normalize stage disabled, skipping")
            return data
        
        from trinn.data.normalize_data import build_normalize_payload
        from trinn.utils.normalize_utils import normalize_title
        
        normalized = build_normalize_payload(data)
        
        # Apply field normalization
        if self.normalize_config.normalize_case:
            for field in self.normalize_config.normalize_fields:
                if field in normalized and isinstance(normalized[field], str):
                    normalized[field] = normalized[field].strip()
        
        # Title normalization
        if "title" in normalized:
            normalized["title"] = normalize_title(normalized["title"])
        
        # Validate required fields
        if self.normalize_config.validate_required_fields:
            if not require_fields(normalized, self.normalize_config.required_fields):
                missing = [f for f in self.normalize_config.required_fields if f not in normalized]
                raise ValidationError(f"Missing required fields: {missing}")
        
        # Store in repository
        await self.normalize_repo.insert(normalized)
        
        logger.debug(f"Normalize stage completed for data: {normalized.get('id', 'unknown')}")
        return normalized
    
    async def _transform_stage(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute transform stage with enterprise processing."""
        if not self.transform_config.enabled:
            logger.debug("Transform stage disabled, skipping")
            return data
        
        from trinn.data.transform_data import build_transform_payload
        from trinn.utils.transform_utils import map_source_to_canonical
        
        transformed = build_transform_payload(data)
        
        # Apply source mapping
        if "source" in transformed:
            canonical_source = map_source_to_canonical(transformed["source"])
            if canonical_source in self.transform_config.canonical_source_mapping:
                transformed["canonical_source"] = self.transform_config.canonical_source_mapping[canonical_source]
            else:
                transformed["canonical_source"] = canonical_source
        
        # Apply field transformations
        for field, transformation in self.transform_config.field_transformations.items():
            if field in transformed:
                transformed[field] = transformation(transformed[field])
        
        # Store in repository
        await self.transform_repo.insert(transformed)
        
        logger.debug(f"Transform stage completed for data: {transformed.get('id', 'unknown')}")
        return transformed
    
    def _update_average_time(self, new_time: float) -> None:
        """Update average processing time with exponential smoothing."""
        alpha = 0.1  # Smoothing factor
        if self.metrics.average_processing_time_ms == 0:
            self.metrics.average_processing_time_ms = new_time
        else:
            self.metrics.average_processing_time_ms = (
                alpha * new_time + (1 - alpha) * self.metrics.average_processing_time_ms
            )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current service metrics for monitoring."""
        return {
            "tasks_processed": self.metrics.tasks_processed,
            "tasks_failed": self.metrics.tasks_failed,
            "pipelines_completed": self.metrics.pipelines_completed,
            "pipelines_failed": self.metrics.pipelines_failed,
            "average_processing_time_ms": self.metrics.average_processing_time_ms,
            "success_rate": self._calculate_success_rate(),
        }
    
    def _calculate_success_rate(self) -> float:
        """Calculate success rate percentage."""
        total = self.metrics.tasks_processed + self.metrics.tasks_failed
        if total == 0:
            return 0.0
        return (self.metrics.tasks_processed / total) * 100
