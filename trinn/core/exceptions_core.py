# f1ndr-backend/trinn/core/exceptions_core.py
"""
DICT-aligned TRINN exceptions with enterprise features.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime


logger = logging.getLogger(__name__)


class TrinnError(Exception):
    """Base TRINN exception with enterprise metadata."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code or "TRINN_ERROR"
        self.context = context or {}
        self.timestamp = datetime.utcnow().isoformat()
        
        # Log the error with enterprise metadata
        logger.error(
            f"TrinnError: {self.error_code} - {self.message} | "
            f"Context: {self.context} | Timestamp: {self.timestamp}"
        )
        
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "context": self.context,
            "timestamp": self.timestamp,
        }


class ValidationError(TrinnError):
    """Validation error with enterprise field details."""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None, **kwargs):
        context = kwargs.get('context', {})
        if field:
            context["field"] = field
        if value is not None:
            context["invalid_value"] = str(value)
        
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            context=context,
        )
        
        self.field = field
        self.invalid_value = value


class ConfigurationError(TrinnError):
    """Configuration error with enterprise config details."""
    
    def __init__(self, message: str, config_key: Optional[str] = None, **kwargs):
        context = kwargs.get('context', {})
        if config_key:
            context["config_key"] = config_key
        
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            context=context,
        )
        
        self.config_key = config_key


class PipelineError(TrinnError):
    """Pipeline execution error with enterprise stage details."""
    
    def __init__(self, message: str, stage: Optional[str] = None, pipeline_id: Optional[str] = None, **kwargs):
        context = kwargs.get('context', {})
        if stage:
            context["stage"] = stage
        if pipeline_id:
            context["pipeline_id"] = pipeline_id
        
        super().__init__(
            message=message,
            error_code="PIPELINE_ERROR",
            context=context,
        )
        
        self.stage = stage
        self.pipeline_id = pipeline_id


class SchedulerError(TrinnError):
    """Scheduler error with enterprise task details."""
    
    def __init__(self, message: str, task_id: Optional[str] = None, **kwargs):
        context = kwargs.get('context', {})
        if task_id:
            context["task_id"] = task_id
        
        super().__init__(
            message=message,
            error_code="SCHEDULER_ERROR",
            context=context,
        )
        
        self.task_id = task_id


class DatabaseError(TrinnError):
    """Database operation error with enterprise query details."""
    
    def __init__(self, message: str, operation: Optional[str] = None, collection: Optional[str] = None, **kwargs):
        context = kwargs.get('context', {})
        if operation:
            context["operation"] = operation
        if collection:
            context["collection"] = collection
        
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            context=context,
        )
        
        self.operation = operation
        self.collection = collection


class RepositoryError(TrinnError):
    """Repository operation error with enterprise data details."""
    
    def __init__(self, message: str, repository: Optional[str] = None, **kwargs):
        context = kwargs.get('context', {})
        if repository:
            context["repository"] = repository
        
        super().__init__(
            message=message,
            error_code="REPOSITORY_ERROR",
            context=context,
        )
        
        self.repository = repository


class ExternalServiceError(TrinnError):
    """External service error with enterprise service details."""
    
    def __init__(self, message: str, service: Optional[str] = None, status_code: Optional[int] = None, **kwargs):
        context = kwargs.get('context', {})
        if service:
            context["service"] = service
        if status_code:
            context["status_code"] = status_code
        
        super().__init__(
            message=message,
            error_code="EXTERNAL_SERVICE_ERROR",
            context=context,
        )
        
        self.service = service
        self.status_code = status_code


def handle_trinn_error(error: Exception) -> Dict[str, Any]:
    """
    Handle TRINN errors with enterprise error formatting.
    
    Args:
        error: Exception to handle
        
    Returns:
        Dictionary with error information for API responses
    """
    if isinstance(error, TrinnError):
        return error.to_dict()
    else:
        # Handle non-TRINN exceptions
        logger.error(f"Unhandled exception: {type(error).__name__} - {str(error)}")
        return {
            "error_code": "UNKNOWN_ERROR",
            "message": str(error),
            "error_type": type(error).__name__,
            "timestamp": datetime.utcnow().isoformat(),
        }
