# f1ndr-backend/api/routes/sellr_routes.py
"""
DICT-aligned sellr API routes with FlutterFlow compatibility and enterprise features.
"""

import logging
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from typing import Any, Dict, Optional
from api.dependencies.auth import owns, require_scopes
from api.schemas.common import Envelope, ModuleStatus, Page, error_responses, ok, paged
from api.schemas.list_schemas import Category, OptCategory, OptSubcategory, Subcategory
from api.schemas.sell_schemas import (
    PhotoContent,
    PhotoOut,
    PhotoSessionCreate,
    PhotoSessionCreated,
    PhotoSessionOut,
    SellListing,
    SellListingCreate,
    SellListingUpdate,
)
from utils.response_builder import error_response
from sellr.config.config import get_listings_config
from sellr.core.core import create_listing, schedule_listing_sync
from sellr.core.photos_core import (
    PhotoError,
    attach_photos,
    close_session,
    create_session,
    fetch_photo,
    fetch_session,
    phone_url,
    photo_content,
    public_session,
    token_session_alive,
    upload_by_token,
)
from sellr.utils.utils import save_listing, update_listing, delete_listing, get_listing, list_listings
from trinn.core.core import cancel_listing_sync


logger = logging.getLogger(__name__)

router = APIRouter(tags=["sellr"])


def _not_found():
    return error_response(message="Listing not found", status_code=404, error_code="NOT_FOUND")


def _photo_not_found():
    return error_response(message="Photo resource not found", status_code=404, error_code="NOT_FOUND")


async def _owned_session(session_id: str, claims: Dict[str, Any]) -> Optional[dict]:
    # Other users' sessions look missing rather than forbidden, so IDs can't be probed.
    session = await fetch_session(session_id)
    if session is None or not owns(claims, session, "owner_id"):
        return None
    return session


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
    
    data = {**listing_data.to_data(), "user_id": claims["sub"]}
    if data.get("photos") is not None:
        try:
            data["photos"] = await attach_photos(claims["sub"], data["photos"])
        except PhotoError as e:
            return error_response(message=str(e), status_code=e.status, error_code=e.code)

    # Use sellr core functionality
    try:
        listing = await create_listing(data)
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
    category: OptCategory = None,
    subcategory: OptSubcategory = None
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
    listing = await get_listing(listing_id)
    await schedule_listing_sync(listing, get_listings_config())  # refresh the snapshot / follow platform changes
    return ok(listing, "Listing updated successfully")


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
    await cancel_listing_sync(listing_id)
    return ok(message="Listing deleted successfully")


# --- Send-to-phone photo sessions -------------------------------------------
# The owner creates a short-lived session from a logged-in device; the phone
# opens phone_url (token in the path, no login) and uploads raw image bytes.

_UPLOAD_PAGE = """<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Add photos</title></head>
<body style="font-family:sans-serif;max-width:34rem;margin:2rem auto;padding:0 1rem">
<h1>Add photos to your listing</h1>
<p>Take photos or choose images; they appear on your other device.</p>
<input id="f" type="file" accept="image/*" capture="environment" multiple>
<pre id="log"></pre>
<script>
const inp = document.getElementById('f'), log = document.getElementById('log');
inp.onchange = async () => {
  for (const file of inp.files) {
    const r = await fetch(location.pathname, {method: 'POST', body: file,
      headers: {'Content-Type': file.type || 'image/jpeg'}});
    log.textContent += file.name + ': ' + (r.ok ? 'uploaded' : 'failed (' + r.status + ')') + '\\n';
  }
};
</script></body></html>"""

_DEAD_LINK_PAGE = """<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Link expired</title></head>
<body style="font-family:sans-serif;max-width:34rem;margin:2rem auto;padding:0 1rem">
<h1>This photo link is no longer active</h1>
<p>Ask for a new photo link on the device where you are creating the listing.</p>
</body></html>"""


@router.post("/photo-sessions", status_code=201, response_model=Envelope[PhotoSessionCreated],
             responses=error_responses(400, 401, 403))
async def create_photo_session(payload: Optional[PhotoSessionCreate] = None,
                               claims: Dict[str, Any] = Depends(_WRITER)):
    """Create a send-to-phone photo session for a listing draft."""
    session, token = await create_session(claims["sub"], payload.listing_id if payload else None)
    return ok(
        {
            "session_id": session["id"],
            "phone_url": phone_url(token),
            "status": session["status"],
            "expires_at": session["expires_at"],
        },
        "Photo session created",
    )


@router.get("/photo-sessions/{session_id}", response_model=Envelope[PhotoSessionOut],
            responses=error_responses(401, 403, 404))
async def get_photo_session(session_id: str, claims: Dict[str, Any] = Depends(_WRITER)):
    """Poll a photo session (owner only): photo metadata lands here as uploads arrive."""
    session = await _owned_session(session_id, claims)
    if session is None:
        return _photo_not_found()
    return ok(await public_session(session), "Photo session retrieved")


@router.post("/photo-sessions/{session_id}/close", response_model=Envelope[PhotoSessionOut],
             responses=error_responses(401, 403, 404))
async def close_photo_session(session_id: str, claims: Dict[str, Any] = Depends(_WRITER)):
    """Close a session early; the phone link stops accepting uploads immediately."""
    session = await _owned_session(session_id, claims)
    if session is None:
        return _photo_not_found()
    return ok(await public_session(await close_session(session)), "Photo session closed")


@router.get("/photos/{photo_id}", response_model=Envelope[PhotoContent],
            responses=error_responses(401, 403, 404))
async def get_photo(photo_id: str, claims: Dict[str, Any] = Depends(_WRITER)):
    """Fetch photo bytes (owner only) as base64 inside the standard envelope."""
    photo = await fetch_photo(photo_id)
    if photo is None or not owns(claims, photo, "owner_id"):
        return _photo_not_found()
    return ok(photo_content(photo), "Photo retrieved")


@router.get("/photo-upload/{token}", response_class=HTMLResponse, include_in_schema=False)
async def photo_upload_page(token: str):
    """Login-less phone upload page; the token in the path is the capability."""
    if not await token_session_alive(token):
        return HTMLResponse(_DEAD_LINK_PAGE, status_code=410)
    return HTMLResponse(_UPLOAD_PAGE)


@router.post("/photo-upload/{token}", response_model=Envelope[PhotoOut],
             responses=error_responses(400, 404, 409, 410, 413, 415))
async def photo_upload(token: str, request: Request):
    """Accept raw image bytes for a live session token; no login required."""
    try:
        meta = await upload_by_token(token, await request.body(), request.headers.get("content-type", ""))
    except PhotoError as e:
        return error_response(message=str(e), status_code=e.status, error_code=e.code)
    return ok(meta, "Photo uploaded")
