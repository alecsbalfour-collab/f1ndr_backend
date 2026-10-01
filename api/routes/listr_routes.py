# f1ndr-backend/api/routes/listr_routes.py
"""
DICT-aligned listr API routes with FlutterFlow compatibility and enterprise features.
"""

import logging
from fastapi import APIRouter, Depends
from api.dependencies.auth import require_scopes
from api.schemas.common import Envelope, ModuleStatus, ok
from api.schemas.list_schemas import ListrPlatform, ListrResult, PlatformList, VehicleIn
from listr.config.config import get_listr_config
from listr.core.core import push_listing, update_listing


logger = logging.getLogger(__name__)

router = APIRouter(tags=["listr"])


@router.get("/status", response_model=Envelope[ModuleStatus])
async def listr_status():
    """
    Get listr module status with FlutterFlow-compatible response.
    
    Returns:
        FlutterFlow-compatible status response
    """
    config = get_listr_config()
    return ok(
        {
            "module": "listr",
            "status": "operational",
            "config": {
                "supported_platforms": config["supported_platforms"],
                "max_title_length": config["max_title_length"],
                "sync_enabled": config["sync_enabled"],
                "sync_interval_hours": config["sync_interval_hours"],
            },
        },
        "Listr module operational",
    )


# Posting to external marketplaces is for dealer accounts.
_PUBLISHER = [Depends(require_scopes("inventory:write"))]


@router.post("/listings", status_code=201, response_model=Envelope[ListrResult], dependencies=_PUBLISHER)
async def push_listing_endpoint(listing_data: VehicleIn, platform: ListrPlatform):
    """
    Push listing to platform with enterprise validation and FlutterFlow compatibility.
    
    Args:
        listing_data: Listing data to push
        platform: Target platform
        
    Returns:
        FlutterFlow-compatible response
    """
    logger.info(f"Pushing listing to platform: {platform}")
    
    # Use listr core functionality
    result = await push_listing(platform, listing_data.to_data())
    
    return ok(result, f"Listing pushed to {platform} successfully")


@router.put("/listings/{listing_id}", response_model=Envelope[ListrResult], dependencies=_PUBLISHER)
async def update_listing_endpoint(listing_id: str, listing_data: VehicleIn, platform: ListrPlatform):
    """
    Update listing on platform with enterprise validation and FlutterFlow compatibility.
    
    Args:
        listing_id: Listing identifier
        listing_data: Updated listing data
        platform: Target platform
        
    Returns:
        FlutterFlow-compatible response
    """
    logger.info(f"Updating listing {listing_id} on platform: {platform}")
    
    # Use listr core functionality
    result = await update_listing(platform, {**listing_data.to_data(), "id": listing_id})
    
    return ok(result, f"Listing updated on {platform} successfully")


@router.get("/platforms", response_model=Envelope[PlatformList])
async def get_platforms():
    """
    Get supported platforms with FlutterFlow compatibility.
    
    Returns:
        FlutterFlow-compatible response with platform list
    """
    config = get_listr_config()
    return ok(
        {
            "platforms": config["supported_platforms"],
            "count": len(config["supported_platforms"]),
        },
        "Supported platforms retrieved",
    )
