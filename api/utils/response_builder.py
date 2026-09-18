# f1ndr-backend/api/utils/response_builder.py
"""
DICT-aligned API response builder with FlutterFlow compatibility and enterprise features.
"""

import logging
from typing import Any, Dict, Optional, List
from datetime import datetime, timezone
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class PaginationMeta:
    """Enterprise pagination metadata for FlutterFlow compatibility."""
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool


def success_response(
    data: Any = None,
    message: str = "Operation successful",
    status_code: int = 200,
    pagination: Optional[PaginationMeta] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Build FlutterFlow-compatible success response with enterprise metadata.
    
    Args:
        data: Response data
        message: Success message
        status_code: HTTP status code
        pagination: Pagination metadata for list responses
        metadata: Additional metadata
        
    Returns:
        Dictionary with FlutterFlow-compatible structure
    """
    response_content = {
        "success": True,
        "message": message,
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    
    # Add pagination if provided (FlutterFlow requires this for list endpoints)
    if pagination:
        response_content["pagination"] = {
            "total": pagination.total,
            "page": pagination.page,
            "page_size": pagination.page_size,
            "total_pages": pagination.total_pages,
            "has_next": pagination.has_next,
            "has_previous": pagination.has_previous,
        }
    
    # Add additional metadata if provided
    if metadata:
        response_content["metadata"] = metadata
    
    logger.debug(f"Success response: {message} (status: {status_code})")
    return response_content


def created_response(
    data: Any = None,
    message: str = "Resource created successfully",
    location: Optional[str] = None
) -> Dict[str, Any]:
    """
    Build FlutterFlow-compatible created response with enterprise metadata.
    
    Args:
        data: Created resource data
        message: Success message
        location: Location header for created resource
        
    Returns:
        Dictionary with FlutterFlow-compatible structure
    """
    response_content = {
        "success": True,
        "message": message,
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    
    if location:
        response_content["location"] = location
    
    logger.info(f"Created response: {message}")
    return response_content


def error_response(
    message: str = "An error occurred",
    status_code: int = 400,
    details: Optional[Any] = None,
    error_code: Optional[str] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Build FlutterFlow-compatible error response with enterprise metadata.
    
    Args:
        message: Error message
        status_code: HTTP status code
        details: Error details
        error_code: Enterprise error code
        request_id: Request ID for tracking
        
    Returns:
        Dictionary with FlutterFlow-compatible error structure
    """
    response_content = {
        "success": False,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    
    # Add error details if provided
    if details:
        response_content["details"] = details
    
    # Add error code if provided
    if error_code:
        response_content["error_code"] = error_code
    
    # Add request ID if provided
    if request_id:
        response_content["request_id"] = request_id
    
    logger.error(f"Error response: {message} (status: {status_code}, code: {error_code})")
    return response_content


def paginated_response(
    data: List[Any],
    total: int,
    page: int = 1,
    page_size: int = 20,
    message: str = "Data retrieved successfully"
) -> Dict[str, Any]:
    """
    Build FlutterFlow-compatible paginated response with enterprise metadata.
    
    Args:
        data: List of items
        total: Total number of items
        page: Current page number
        page_size: Number of items per page
        message: Success message
        
    Returns:
        Dictionary with FlutterFlow-compatible pagination structure
    """
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    
    pagination = PaginationMeta(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1,
    )
    
    return success_response(
        data=data,
        message=message,
        pagination=pagination,
    )


def validation_error_response(
    errors: Dict[str, List[str]],
    message: str = "Validation failed"
) -> Dict[str, Any]:
    """
    Build FlutterFlow-compatible validation error response.
    
    Args:
        errors: Dictionary of field errors
        message: Error message
        
    Returns:
        Dictionary with FlutterFlow-compatible validation structure
    """
    return error_response(
        message=message,
        status_code=422,
        details={"validation_errors": errors},
        error_code="VALIDATION_ERROR"
    )


def not_found_response(
    resource: str = "Resource",
    resource_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Build FlutterFlow-compatible not found response.
    
    Args:
        resource: Resource type name
        resource_id: Resource identifier
        
    Returns:
        Dictionary with FlutterFlow-compatible not found structure
    """
    message = f"{resource} not found"
    if resource_id:
        message += f" with ID: {resource_id}"
    
    return error_response(
        message=message,
        status_code=404,
        error_code="NOT_FOUND"
    )
