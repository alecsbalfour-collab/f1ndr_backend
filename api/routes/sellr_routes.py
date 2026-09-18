# f1ndr-backend/api/routes/sellr_routes.py
"""
DICT-aligned sellr API routes with FlutterFlow compatibility and enterprise features.
"""

import logging
from fastapi import APIRouter, Query, HTTPException
from typing import Dict, Any, Optional
from utils.response_builder import success_response, error_response, paginated_response
from sellr.config.config import get_listings_config
from sellr.core.core import create_listing
from sellr.utils.utils import save_listing, update_listing, delete_listing, get_listing, get_user_listings


logger = logging.getLogger(__name__)

router = APIRouter(tags=["sellr"])


@router.get("/status")
async def sellr_status() -> Dict[str, Any]:
    """
    Get sellr module status with FlutterFlow-compatible response.
    
    Returns:
        FlutterFlow-compatible status response
    """
    try:
        config = get_listings_config()
        
        return success_response(
            data={
                "module": "sellr",
                "status": "operational",
                "config": {
                    "max_title_length": config["max_title_length"],
                    "min_price": config["min_price"],
                    "enable_vin_autofill": config["enable_vin_autofill"],
                    "allow_multi_platform": config["allow_multi_platform"],
                    "default_platforms": config["default_platforms"],
                },
            },
            message="Sellr module operational"
        )
        
    except Exception as e:
        logger.error(f"Failed to get sellr status: {e}")
        return error_response(
            message=f"Failed to get status: {str(e)}",
            status_code=500,
            error_code="STATUS_ERROR"
        )


@router.post("/listings")
async def create_listing_endpoint(listing_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create listing with enterprise validation and FlutterFlow compatibility.
    
    Args:
        listing_data: Listing creation data
        
    Returns:
        FlutterFlow-compatible response with created listing
    """
    try:
        logger.info(f"Creating listing: {listing_data.get('title', 'unknown')}")
        
        # Use sellr core functionality
        listing = create_listing(listing_data)
        
        # Save to database
        listing_id = save_listing(listing)
        listing["id"] = listing_id
        
        return success_response(
            data=listing,
            message="Listing created successfully",
            status_code=201
        )
        
    except Exception as e:
        logger.error(f"Create listing failed: {e}")
        return error_response(
            message=f"Failed to create listing: {str(e)}",
            status_code=500,
            error_code="CREATE_LISTING_ERROR"
        )


@router.get("/listings")
async def get_listings(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    platform: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get listings with FlutterFlow-compatible pagination and filtering.
    
    Args:
        page: Page number (default: 1)
        page_size: Number of results per page (default: 20)
        user_id: Optional user ID filter
        status: Optional status filter
        platform: Optional platform filter
        
    Returns:
        FlutterFlow-compatible paginated response
    """
    try:
        logger.info(f"Getting listings - page: {page}, user_id: {user_id}, status: {status}")
        
        if user_id:
            # Get user-specific listings
            result = get_user_listings(user_id, status, page, page_size)
            return success_response(
                data=result,
                message="User listings retrieved"
            )
        else:
            # Get all listings with filters
            # TODO: Implement general listing query
            results = []
            total = 0
            
            return paginated_response(
                data=results,
                total=total,
                page=page,
                page_size=page_size,
                message="Listings retrieved"
            )
        
    except Exception as e:
        logger.error(f"Get listings failed: {e}")
        return error_response(
            message=f"Failed to get listings: {str(e)}",
            status_code=500,
            error_code="GET_LISTINGS_ERROR"
        )


@router.get("/listings/{listing_id}")
async def get_listing_endpoint(listing_id: str) -> Dict[str, Any]:
    """
    Get listing by ID with FlutterFlow compatibility.
    
    Args:
        listing_id: Listing identifier
        
    Returns:
        FlutterFlow-compatible response with listing data
    """
    try:
        logger.info(f"Getting listing: {listing_id}")
        
        listing = get_listing(listing_id)
        
        if listing:
            return success_response(
                data=listing,
                message="Listing retrieved"
            )
        else:
            return error_response(
                message="Listing not found",
                status_code=404,
                error_code="NOT_FOUND"
            )
        
    except Exception as e:
        logger.error(f"Get listing failed: {e}")
        return error_response(
            message=f"Failed to get listing: {str(e)}",
            status_code=500,
            error_code="GET_LISTING_ERROR"
        )


@router.put("/listings/{listing_id}")
async def update_listing_endpoint(listing_id: str, listing_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update listing with enterprise validation and FlutterFlow compatibility.
    
    Args:
        listing_id: Listing identifier
        listing_data: Updated listing data
        
    Returns:
        FlutterFlow-compatible response with updated listing
    """
    try:
        logger.info(f"Updating listing: {listing_id}")
        
        success = update_listing(listing_id, listing_data)
        
        if success:
            return success_response(
                data=listing_data,
                message="Listing updated successfully"
            )
        else:
            return error_response(
                message="Failed to update listing",
                status_code=500,
                error_code="UPDATE_FAILED"
            )
        
    except Exception as e:
        logger.error(f"Update listing failed: {e}")
        return error_response(
            message=f"Failed to update listing: {str(e)}",
            status_code=500,
            error_code="UPDATE_LISTING_ERROR"
        )


@router.delete("/listings/{listing_id}")
async def delete_listing_endpoint(listing_id: str) -> Dict[str, Any]:
    """
    Delete listing with enterprise safety checks and FlutterFlow compatibility.
    
    Args:
        listing_id: Listing identifier
        
    Returns:
        FlutterFlow-compatible response
    """
    try:
        logger.info(f"Deleting listing: {listing_id}")
        
        success = delete_listing(listing_id)
        
        if success:
            return success_response(
                message="Listing deleted successfully"
            )
        else:
            return error_response(
                message="Failed to delete listing",
                status_code=500,
                error_code="DELETE_FAILED"
            )
        
    except Exception as e:
        logger.error(f"Delete listing failed: {e}")
        return error_response(
            message=f"Failed to delete listing: {str(e)}",
            status_code=500,
            error_code="DELETE_LISTING_ERROR"
        )
