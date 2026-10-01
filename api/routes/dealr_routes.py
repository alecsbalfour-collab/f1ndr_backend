# f1ndr-backend/api/routes/dealr_routes.py
"""
DICT-aligned dealr API routes with FlutterFlow compatibility and enterprise features.
"""

import logging
from fastapi import APIRouter, Depends, Query
from typing import Any, Dict, Optional
from api.dependencies.auth import is_admin, owns, require_scopes
from api.schemas.common import Envelope, ModuleStatus, Page, error_responses, ok, paged
from api.schemas.dealr_schemas import InventoryIn, InventoryItem
from utils.response_builder import error_response
from dealr.config.dealr_config import dealr_config
from dealr.core.core import ingest_inventory, sync_inventory
from dealr.db import inventory_repo


logger = logging.getLogger(__name__)

router = APIRouter(tags=["dealr"])

_READER = require_scopes("inventory:read")
_WRITER = require_scopes("inventory:write")


def _not_found():
    return error_response(message="Inventory not found", status_code=404, error_code="NOT_FOUND")


@router.get("/status", response_model=Envelope[ModuleStatus])
async def dealr_status():
    """
    Get dealr module status with FlutterFlow-compatible response.
    
    Returns:
        FlutterFlow-compatible status response
    """
    return ok(
        {
            "module": "dealr",
            "status": "operational",
            "feature_key": dealr_config["feature_key"],
            "feature_version": dealr_config["feature_version"],
            "enabled": dealr_config["enabled"],
        },
        "dealr module operational",
    )


@router.post("/inventory", status_code=201, response_model=Envelope[InventoryItem],
             responses=error_responses(401, 403))
async def create_inventory(inventory_data: InventoryIn, claims: Dict[str, Any] = Depends(_WRITER)):
    """
    Create inventory with enterprise validation and FlutterFlow compatibility.
    
    Args:
        inventory_data: Inventory creation data
        
    Returns:
        FlutterFlow-compatible response with created inventory
    """
    logger.info(f"Creating inventory: {inventory_data.name or 'unknown'}")
    processed_data = await ingest_inventory({**inventory_data.to_data(), "owner_id": claims["sub"]})
    return ok(processed_data, "Inventory created successfully")


@router.get("/inventory", response_model=Page[InventoryItem], responses=error_responses(401, 403))
async def get_inventory(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    claims: Dict[str, Any] = Depends(_READER),
):
    """
    Get inventory with FlutterFlow-compatible pagination.
    
    Args:
        page: Page number (default: 1)
        page_size: Number of results per page (default: 20)
        status: Optional status filter
        
    Returns:
        FlutterFlow-compatible paginated response
    """
    logger.info(f"Getting inventory - page: {page}, status: {status}")
    # Dealers see their own inventory; admins see everything.
    owner_id = None if is_admin(claims) else claims["sub"]
    result = await inventory_repo.list_inventory(status, page, page_size, owner_id=owner_id)
    return paged(result["items"], result["total"], page, page_size, "Inventory retrieved")


@router.put("/inventory/{inventory_id}", response_model=Envelope[InventoryItem],
            responses=error_responses(401, 403, 404))
async def update_inventory(inventory_id: str, inventory_data: InventoryIn, claims: Dict[str, Any] = Depends(_WRITER)):
    """
    Update inventory with enterprise validation and FlutterFlow compatibility.
    
    Args:
        inventory_id: Inventory identifier
        inventory_data: Updated inventory data
        
    Returns:
        FlutterFlow-compatible response with updated inventory
    """
    logger.info(f"Updating inventory: {inventory_id}")
    existing = await inventory_repo.get_inventory(inventory_id)
    if existing is not None and not owns(claims, existing, "owner_id"):
        return _not_found()
    owner_id = existing.get("owner_id") if existing else claims["sub"]
    processed_data = await sync_inventory({**inventory_data.to_data(), "id": inventory_id, "owner_id": owner_id})
    return ok(processed_data, "Inventory updated successfully")


@router.delete("/inventory/{inventory_id}", response_model=Envelope[None],
               responses=error_responses(401, 403, 404))
async def delete_inventory(inventory_id: str, claims: Dict[str, Any] = Depends(_WRITER)):
    """
    Delete inventory with enterprise safety checks and FlutterFlow compatibility.
    
    Args:
        inventory_id: Inventory identifier
        
    Returns:
        FlutterFlow-compatible response
    """
    logger.info(f"Deleting inventory: {inventory_id}")
    existing = await inventory_repo.get_inventory(inventory_id)
    if existing is None or not owns(claims, existing, "owner_id") or not await inventory_repo.delete_inventory(inventory_id):
        return _not_found()
    return ok(message="Inventory deleted successfully")
