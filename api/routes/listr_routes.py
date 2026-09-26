# f1ndr-backend/api/routes/listr_routes.py
"""
DICT-aligned listr API routes with FlutterFlow compatibility and enterprise features.
"""

import logging
from fastapi import APIRouter, Query, HTTPException
from typing import Dict, Any, Optional
from utils.response_builder import success_response, error_response, paginated_response
from listr.config.config import get_listr_config
from listr.core.core import push_listing, update_listing


logger = logging.getLogger(__name__)

router = APIRouter(tags=["listr"])


@router.get("/status")
async def listr_status() -> Dict[str, Any]:
    """
    Get listr module status with FlutterFlow-compatible response.
    
    Returns:
        FlutterFlow-compatible status response
    """
    try:
        config = get_listr_config()
        
        return success_response(
            data={
                "module": "listr",
                "status": "operational",
                "config": {
                    "supported_platforms": config["supported_platforms"],
                    "max_title_length": config["max_title_length"],
                    "sync_enabled": config["sync_enabled"],
                    "sync_interval_hours": config["sync_interval_hours"],
                },
            },
            message="Listr module operational"
        )
        
    except Exception as e:
        logger.error(f"Failed to get listr status: {e}")
        return error_response(
            message=f"Failed to get status: {str(e)}",
            status_code=500,
            error_code="STATUS_ERROR"
        )


@router.post("/listings")
async def push_listing_endpoint(listing_data: Dict[str, Any], platform: str) -> Dict[str, Any]:
    """
    Push listing to platform with enterprise validation and FlutterFlow compatibility.
    
    Args:
        listing_data: Listing data to push
        platform: Target platform
        
    Returns:
        FlutterFlow-compatible response
    """
    try:
        logger.info(f"Pushing listing to platform: {platform}")
        
        # Use listr core functionality
        result = await push_listing(platform, listing_data)
        
        return success_response(
            data=result,
            message=f"Listing pushed to {platform} successfully",
            status_code=201
        )
        
    except Exception as e:
        logger.error(f"Push listing failed: {e}")
        return error_response(
            message=f"Failed to push listing: {str(e)}",
            status_code=500,
            error_code="PUSH_LISTING_ERROR"
        )


@router.put("/listings/{listing_id}")
async def update_listing_endpoint(listing_id: str, listing_data: Dict[str, Any], platform: str) -> Dict[str, Any]:
    """
    Update listing on platform with enterprise validation and FlutterFlow compatibility.
    
    Args:
        listing_id: Listing identifier
        listing_data: Updated listing data
        platform: Target platform
        
    Returns:
        FlutterFlow-compatible response
    """
    try:
        logger.info(f"Updating listing {listing_id} on platform: {platform}")
        
        # Use listr core functionality
        result = await update_listing(platform, {**listing_data, "id": listing_id})
        
        return success_response(
            data=result,
            message=f"Listing updated on {platform} successfully"
        )
        
    except Exception as e:
        logger.error(f"Update listing failed: {e}")
        return error_response(
            message=f"Failed to update listing: {str(e)}",
            status_code=500,
            error_code="UPDATE_LISTING_ERROR"
        )


@router.get("/platforms")
async def get_platforms() -> Dict[str, Any]:
    """
    Get supported platforms with FlutterFlow compatibility.
    
    Returns:
        FlutterFlow-compatible response with platform list
    """
    try:
        config = get_listr_config()
        
        return success_response(
            data={
                "platforms": config["supported_platforms"],
                "count": len(config["supported_platforms"]),
            },
            message="Supported platforms retrieved"
        )
        
    except Exception as e:
        logger.error(f"Failed to get platforms: {e}")
        return error_response(
            message=f"Failed to get platforms: {str(e)}",
            status_code=500,
            error_code="GET_PLATFORMS_ERROR"
        )
