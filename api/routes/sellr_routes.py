# f1ndr-backend/api/routes/sellr_routes.py
"""
DICT-aligned sellr API routes with FlutterFlow compatibility and enterprise features.
"""

import logging
from fastapi import APIRouter, Depends, Query
from typing import Any, Dict, Optional
from api.dependencies.auth import owns, require_scopes
from api.schemas.common import Envelope, ModuleStatus, Page, error_responses, ok, paged
from api.schemas.list_schemas import Category, Subcategory
from api.schemas.sell_schemas import SellListing, SellListingCreate, SellListingUpdate
from utils.response_builder import error_response
from sellr.config.config import get_listings_config
from sellr.core.core import create_listing
from sellr.utils.utils import save_listing, update_listing, delete_listing, get_listing, list_listings


logger = logging.getLogger(__name__)

router = APIRouter(tags=["sellr"])


def _not_found():
    return error_response(message="Listing not found", status_code=404, error_code="NOT_FOUND")


async def _owned(listing_id: str, claims: Dict[str, Any]) -> bool:
    # Other sellers' listings look missing rather than forbidden, so IDs can't be probed.
    listing = await get_listing(listing_id)
    return listing is not None and owns(claims, listing, "user_id")


@router.get("/status", response_model=Envelope[ModuleStatus])
async def sellr_status():
    """
    Get sellr module status with FlutterFlow-compatible response.
    
    Returns:
        FlutterFlow-compatible status response
    """
    config = get_listings_config()
    return ok(
        {
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
        "Sellr module operational",
    )


_WRITER = require_scopes("listings:write")


@router.post("/listings", status_code=201, response_model=Envelope[SellListing], responses=error_responses(400, 401, 403))
async def create_listing_endpoint(listing_data: SellListingCreate, claims: Dict[str, Any] = Depends(_WRITER)):
    """
    Create listing with enterprise validation and FlutterFlow compatibility.
    
    Args:
        listing_data: Listing creation data
        
    Returns:
        FlutterFlow-compatible response with created listing
    """
    logger.info(f"Creating listing: {listing_data.title}")
    
    # Use sellr core functionality
    try:
        listing = await create_listing({**listing_data.to_data(), "user_id": claims["sub"]})
    except ValueError as e:
        # Business-rule messages raised by sellr.core (e.g. price below the configured minimum)
        return error_response(message=str(e), status_code=400, error_code="INVALID_LISTING")
    
    # Save to database
    listing_id = await save_listing(listing)
    listing["id"] = listing_id
    
    return ok(listing, "Listing created successfully")


@router.get("/listings", response_model=Page[SellListing])
async def get_listings(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    platform: Optional[str] = None,
    category: Optional[Category] = None,
    subcategory: Optional[Subcategory] = None
):
    """
    Get listings with FlutterFlow-compatible pagination and filtering.
    
    Args:
        page: Page number (default: 1)
        page_size: Number of results per page (default: 20)
        user_id: Optional user ID filter
        status: Optional status filter
        platform: Optional platform filter
        category: Optional classifieds category filter
        subcategory: Optional subcategory filter
        
    Returns:
        FlutterFlow-compatible paginated response
    """
    logger.info(
        f"Getting listings - page: {page}, user_id: {user_id}, status: {status}, "
        f"category: {category}, subcategory: {subcategory}"
    )

    result = await list_listings(
        {"user_id": user_id, "status": status, "platform": platform,
         "category": category, "subcategory": subcategory},
        page, page_size,
    )
    return paged(result["listings"], result["total"], page, page_size, "Listings retrieved")


@router.get("/listings/{listing_id}", response_model=Envelope[SellListing], responses=error_responses(404))
async def get_listing_endpoint(listing_id: str):
    """
    Get listing by ID with FlutterFlow compatibility.
    
    Args:
        listing_id: Listing identifier
        
    Returns:
        FlutterFlow-compatible response with listing data
    """
    logger.info(f"Getting listing: {listing_id}")
    
    listing = await get_listing(listing_id)
    return ok(listing, "Listing retrieved") if listing else _not_found()


@router.put("/listings/{listing_id}", response_model=Envelope[SellListing], responses=error_responses(401, 403, 404))
async def update_listing_endpoint(listing_id: str, listing_data: SellListingUpdate, claims: Dict[str, Any] = Depends(_WRITER)):
    """
    Update listing with enterprise validation and FlutterFlow compatibility.
    
    Args:
        listing_id: Listing identifier
        listing_data: Updated listing data
        
    Returns:
        FlutterFlow-compatible response with updated listing
    """
    logger.info(f"Updating listing: {listing_id}")
    
    if not await _owned(listing_id, claims) or not await update_listing(listing_id, listing_data.to_data()):
        return _not_found()
    return ok(await get_listing(listing_id), "Listing updated successfully")


@router.delete("/listings/{listing_id}", response_model=Envelope[None], responses=error_responses(401, 403, 404))
async def delete_listing_endpoint(listing_id: str, claims: Dict[str, Any] = Depends(_WRITER)):
    """
    Delete listing with enterprise safety checks and FlutterFlow compatibility.
    
    Args:
        listing_id: Listing identifier
        
    Returns:
        FlutterFlow-compatible response
    """
    logger.info(f"Deleting listing: {listing_id}")
    
    if not await _owned(listing_id, claims) or not await delete_listing(listing_id):
        return _not_found()
    return ok(message="Listing deleted successfully")
