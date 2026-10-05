# f1ndr-backend/api/routes/controllers/list_controller.py
"""
DICT-aligned list controller with FlutterFlow compatibility and enterprise features.
"""

import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Query
from api.schemas.common import Page, paged
from api.schemas.list_schemas import Category, ComparisonGroup, OptCategory, OptSubcategory, Subcategory, VehicleOut
from f1ndr.db.db import listings_store as f1ndr_store
from f1ndr.utils.utils import group_equivalent_listings
from listr.db.listing_repo import listings_store as listr_store
from sellr.utils.utils import listings_store as sellr_store
from utils.response_builder import success_response, error_response, paginated_response


logger = logging.getLogger(__name__)

# Router for listings
router = APIRouter(prefix="/listings", tags=["listings"])


@router.get("/unified", response_model=Page[VehicleOut])
async def get_unified_listings(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    category: OptCategory = None,
    subcategory: OptSubcategory = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    region: Optional[str] = None,
    location: Optional[str] = None
):
    """
    Get unified listings from all platforms with FlutterFlow-compatible pagination.

    Args:
        page: Page number (default: 1)
        page_size: Number of results per page (default: 20)
        search: Optional search query
        category: Optional category filter
        subcategory: Optional subcategory filter
        min_price: Optional minimum price filter
        max_price: Optional maximum price filter

    Returns:
        FlutterFlow-compatible paginated response
    """
    logger.info(f"Getting unified listings - page: {page}, filters: {search}, {category}, {subcategory}")

    docs = await _merged_listing_docs(category=category, subcategory=subcategory, region=region)

    if search:
        needle = search.lower()
        docs = [d for d in docs
                if needle in " ".join(str(d.get(f) or "") for f in ("title", "description", "make", "model", "location")).lower()]
    if location:
        needle = location.lower()
        docs = [d for d in docs if needle in str(d.get("location") or "").lower()]
    if min_price is not None:
        docs = [d for d in docs if (d.get("price") or 0) >= min_price]
    if max_price is not None:
        docs = [d for d in docs if (d.get("price") or 0) <= max_price]

    docs.sort(key=lambda d: d.get("scraped_at") or d.get("created_at") or "", reverse=True)
    total = len(docs)
    results = docs[(page - 1) * page_size: page * page_size]

    return paged(results, total, page, page_size, "Unified listings retrieved")


async def _merged_listing_docs(category=None, subcategory=None, region=None) -> list:
    """Sellr + listr + scraped-corpus docs, deduped by listing id."""
    query = {k: v for k, v in {"category": category, "subcategory": subcategory, "region": region}.items() if v}
    seen, docs = set(), []
    for store in (sellr_store, listr_store, f1ndr_store):
        for doc in await store.find(query, limit=10_000):
            key = doc.get("id") or doc.get("key") or id(doc)
            if key not in seen:
                seen.add(key)
                docs.append(doc)
    return docs


@router.get("/compare", response_model=Page[ComparisonGroup])
async def get_comparison_groups(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    category: OptCategory = None,
    subcategory: OptSubcategory = None,
    region: Optional[str] = None,
    listing_id: Optional[str] = None,
    title_threshold: float = Query(0.6, ge=0.3, le=1.0),
    price_delta: float = Query(0.15, ge=0.0, le=1.0),
):
    """Group listings believed to be the same item across platforms/sellers.

    Two listings cluster when they share category+region, their titles are similar
    (normalized tokens, `title_threshold` Jaccard), structured fields agree when both
    are set (year/make/model), and prices fall within `price_delta` of each other.
    `listing_id` scopes the result to the group containing that listing.
    """
    docs = await _merged_listing_docs(category=category, subcategory=subcategory, region=region)
    if search:
        needle = search.lower()
        docs = [d for d in docs
                if needle in " ".join(str(d.get(f) or "") for f in ("title", "description", "make", "model", "location")).lower()]

    groups = group_equivalent_listings(docs, title_threshold=title_threshold, price_delta=price_delta)
    if listing_id:
        groups = [g for g in groups if any(d.get("id") == listing_id for d in g["listings"])]

    total = len(groups)
    results = groups[(page - 1) * page_size: page * page_size]
    return paged(results, total, page, page_size, "Comparison groups retrieved")


# Platform spellings differ between listr pushes and scraper source names.
_PLATFORM_ALIASES = {
    "facebook": {"facebook", "facebook_marketplace"},
}


async def _raw_platform_listings(platform: str, page: int, page_size: int) -> dict:
    # A platform's raw feed is both what listr pushed there and what the scrapers collected.
    names = _PLATFORM_ALIASES.get(platform, {platform})
    seen, docs = set(), []
    for name in names:
        for store in (listr_store, f1ndr_store):
            for doc in await store.find({"platform": name}, limit=10_000):
                key = doc.get("id") or doc.get("key") or id(doc)
                if key not in seen:
                    seen.add(key)
                    docs.append(doc)
    docs.sort(key=lambda d: d.get("scraped_at") or d.get("updated_at") or "", reverse=True)
    total = len(docs)
    results = docs[(page - 1) * page_size: page * page_size]
    return paged(results, total, page, page_size, f"{platform.capitalize()} listings retrieved")


@router.get("/raw/facebook", response_model=Page[VehicleOut])
async def get_raw_facebook_listings(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """Get raw Facebook listings with FlutterFlow-compatible pagination."""
    logger.info(f"Getting raw Facebook listings - page: {page}")
    return await _raw_platform_listings("facebook", page, page_size)


@router.get("/raw/kijiji", response_model=Page[VehicleOut])
async def get_raw_kijiji_listings(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """Get raw Kijiji listings with FlutterFlow-compatible pagination."""
    logger.info(f"Getting raw Kijiji listings - page: {page}")
    return await _raw_platform_listings("kijiji", page, page_size)


@router.get("/raw/craigslist", response_model=Page[VehicleOut])
async def get_raw_craigslist_listings(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """Get raw Craigslist listings with FlutterFlow-compatible pagination."""
    logger.info(f"Getting raw Craigslist listings - page: {page}")
    return await _raw_platform_listings("craigslist", page, page_size)


class ListController:
    """Enterprise list controller with DICT patterns and FlutterFlow compatibility."""
    
    def __init__(self):
        logger.info("ListController initialized")
    
    def search(self, query: str, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """
        Search listings with FlutterFlow-compatible pagination.
        
        Args:
            query: Search query string
            page: Page number (default: 1)
            page_size: Number of results per page (default: 20)
            
        Returns:
            FlutterFlow-compatible paginated response
        """
        try:
            logger.info(f"Listing search query: {query}, page: {page}, page_size: {page_size}")
            
            # TODO: Implement actual search functionality
            results = []
            total = 0
            
            return paginated_response(
                data=results,
                total=total,
                page=page,
                page_size=page_size,
                message=f"Listing search completed for query: {query}"
            )
            
        except Exception as e:
            logger.error(f"Listing search failed: {e}")
            return error_response(
                message="Search failed",
                status_code=500,
                error_code="LISTING_SEARCH_ERROR"
            )


list_controller = ListController()
