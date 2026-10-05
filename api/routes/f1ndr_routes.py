# f1ndr-backend/api/routes/f1ndr_routes.py
"""
DICT-aligned f1ndr API routes with FlutterFlow compatibility and enterprise features.
"""

import logging
from fastapi import APIRouter, Depends, Query
from api.dependencies.auth import require_user
from typing import Optional
from api.schemas.common import VIN, Envelope, ModuleStatus, Page, ok, paged
from api.schemas.list_schemas import Category, OptCategory, OptSubcategory, Subcategory, VehicleIn, VehicleOut
from api.schemas.search_schema import IntelligenceResult, MarketValue, SearchRequest, SearchResults, VinDecodeRequest, VinDecodeResult
from f1ndr.vin.decode import decode_vin
from f1ndr.config.config import get_f1ndr_config
from f1ndr.core.core import run_search, run_intelligence
from f1ndr.db.db import listings_store


logger = logging.getLogger(__name__)

router = APIRouter(tags=["f1ndr"])


@router.get("/status", response_model=Envelope[ModuleStatus])
async def f1ndr_status():
    """
    Get f1ndr module status with FlutterFlow-compatible response.
    
    Returns:
        FlutterFlow-compatible status response
    """
    config = get_f1ndr_config()
    return ok(
        {
            "module": "f1ndr",
            "status": "operational",
            "config": {
                "api_version": config.get("api_version", "1.0.0"),
                "enabled_features": config.get("enabled_features", []),
            },
        },
        "F1NDR module operational",
    )


# Authenticated: each call makes an outbound request to NHTSA.
@router.post("/vin/decode", response_model=Envelope[VinDecodeResult], dependencies=[Depends(require_user)])
async def decode_vin_endpoint(vin_data: VinDecodeRequest):
    """
    Decode VIN with enterprise validation and FlutterFlow compatibility.
    
    Args:
        vin_data: VIN data containing VIN string
        
    Returns:
        FlutterFlow-compatible response with decoded VIN data
    """
    logger.info(f"Decoding VIN: {vin_data.vin}")
    
    # Use f1ndr core functionality
    decoded = decode_vin(vin_data.vin)
    
    return ok(decoded, "VIN decoded successfully")


@router.get("/vehicles", response_model=Page[VehicleOut])
async def get_vehicles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: OptCategory = None,
    subcategory: OptSubcategory = None,
    make: Optional[str] = None,
    model: Optional[str] = None,
    year: Optional[int] = None
):
    """
    Get vehicles with FlutterFlow-compatible pagination and filtering.

    Args:
        page: Page number (default: 1)
        page_size: Number of results per page (default: 20)
        category: Optional classifieds category filter
        subcategory: Optional subcategory filter
        make: Optional make filter
        model: Optional model filter
        year: Optional year filter

    Returns:
        FlutterFlow-compatible paginated response
    """
    logger.info(f"Getting vehicles - page: {page}, category: {category}, subcategory: {subcategory}, make: {make}, model: {model}, year: {year}")

    filters = {"category": category, "subcategory": subcategory, "make": make, "model": model, "year": year}
    query = {k: v for k, v in filters.items() if v is not None}
    results = await listings_store.find(query, skip=(page - 1) * page_size, limit=page_size)
    total = await listings_store.count(query)

    return paged(results, total, page, page_size, "Vehicles retrieved")


@router.post("/search", response_model=Envelope[SearchResults])
async def search_endpoint(params: SearchRequest):
    return ok(await run_search(params.model_dump(exclude_none=True)), "Search completed")


# Authenticated: the enriched listing is persisted.
@router.post("/intelligence", response_model=Envelope[IntelligenceResult], dependencies=[Depends(require_user)])
async def intelligence_endpoint(listing: VehicleIn):
    return ok(await run_intelligence(listing.to_data()), "Intelligence completed")


@router.get("/market/value", response_model=Envelope[MarketValue])
async def get_market_value(vin: VIN, mileage: Optional[int] = Query(None, ge=0)):
    """
    Get market value for vehicle with enterprise validation and FlutterFlow compatibility.
    
    Args:
        vin: Vehicle VIN
        mileage: Optional vehicle mileage
        
    Returns:
        FlutterFlow-compatible response with market value data
    """
    logger.info(f"Getting market value for VIN: {vin}, mileage: {mileage}")

    # No pricing provider yet (Pricing roadmap item); null so clients don't show $0.
    market_data = {
        "vin": vin,
        "market_value": None,
        "confidence": 0.0,
        "mileage": mileage,
    }

    return ok(market_data, "Market value unavailable")
