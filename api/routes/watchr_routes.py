# f1ndr-backend/api/routes/watchr_routes.py
"""
DICT-aligned watchr API routes with FlutterFlow compatibility and enterprise features.
"""

import logging
from fastapi import APIRouter, Depends, Query
from typing import Any, Dict, Optional
from api.dependencies.auth import owns, require_user
from api.schemas.common import Envelope, ModuleStatus, Page, error_responses, ok, paged
from api.schemas.watch_schemas import Alert, AlertOut, Subscription, SubscriptionOut
from utils.response_builder import error_response
from watchr.core import core as watchr_core


logger = logging.getLogger(__name__)

router = APIRouter(tags=["watchr"])


@router.get("/status", response_model=Envelope[ModuleStatus])
async def watchr_status():
    """
    Get watchr module status with FlutterFlow-compatible response.
    
    Returns:
        FlutterFlow-compatible status response
    """
    return ok(
        {
            "module": "watchr",
            "status": "operational",
            "features": {
                "alert_system": True,
                "subscription_management": True,
                "real_time_monitoring": True,
            },
        },
        "Watchr module operational",
    )


def _not_found(kind: str = "Alert"):
    return error_response(message=f"{kind} not found", status_code=404, error_code="NOT_FOUND")


@router.post("/alerts", status_code=201, response_model=Envelope[AlertOut], responses=error_responses(401))
async def create_alert(alert_data: Alert, claims: Dict[str, Any] = Depends(require_user)):
    """
    Create alert with enterprise validation and FlutterFlow compatibility.

    Args:
        alert_data: Alert creation data

    Returns:
        FlutterFlow-compatible response with created alert
    """
    logger.info(f"Creating alert: {alert_data.name}")
    alert = await watchr_core.create_alert({**alert_data.to_data(), "user_id": claims["sub"]})
    return ok(alert, "Alert created successfully")


@router.get("/alerts", response_model=Page[AlertOut], responses=error_responses(401))
async def get_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    claims: Dict[str, Any] = Depends(require_user),
):
    """
    Get alerts with FlutterFlow-compatible pagination and filtering.

    Args:
        page: Page number (default: 1)
        page_size: Number of results per page (default: 20)
        status: Optional status filter

    Returns:
        FlutterFlow-compatible paginated response
    """
    logger.info(f"Getting alerts - page: {page}, user_id: {claims['sub']}, status: {status}")
    result = await watchr_core.list_alerts(claims["sub"], status, page, page_size)
    return paged(result["alerts"], result["total"], page, page_size, "Alerts retrieved")


@router.delete("/alerts/{alert_id}", response_model=Envelope[None], responses=error_responses(401, 404))
async def delete_alert(alert_id: str, claims: Dict[str, Any] = Depends(require_user)):
    """
    Delete alert with enterprise safety checks and FlutterFlow compatibility.

    Args:
        alert_id: Alert identifier

    Returns:
        FlutterFlow-compatible response
    """
    logger.info(f"Deleting alert: {alert_id}")
    alert = await watchr_core.get_alert(alert_id)
    if alert is None or not owns(claims, alert, "user_id") or not await watchr_core.delete_alert(alert_id):
        return _not_found()
    return ok(message="Alert deleted successfully")


@router.post("/subscriptions", status_code=201, response_model=Envelope[SubscriptionOut], responses=error_responses(401))
async def create_subscription(subscription_data: Subscription, claims: Dict[str, Any] = Depends(require_user)):
    """
    Create subscription with enterprise validation and FlutterFlow compatibility.

    Args:
        subscription_data: Subscription creation data

    Returns:
        FlutterFlow-compatible response with created subscription
    """
    logger.info(f"Creating subscription: {subscription_data.name}")
    subscription = await watchr_core.create_subscription({**subscription_data.to_data(), "user_id": claims["sub"]})
    return ok(subscription, "Subscription created successfully")


@router.get("/subscriptions", response_model=Page[SubscriptionOut], responses=error_responses(401))
async def get_subscriptions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    claims: Dict[str, Any] = Depends(require_user),
):
    """Get the caller's subscriptions with FlutterFlow-compatible pagination."""
    result = await watchr_core.list_subscriptions(claims["sub"], page, page_size)
    return paged(result["subscriptions"], result["total"], page, page_size, "Subscriptions retrieved")


@router.delete("/subscriptions/{subscription_id}", response_model=Envelope[None], responses=error_responses(401, 404))
async def delete_subscription(subscription_id: str, claims: Dict[str, Any] = Depends(require_user)):
    """Delete one of the caller's subscriptions."""
    logger.info(f"Deleting subscription: {subscription_id}")
    subscription = await watchr_core.get_subscription(subscription_id)
    if subscription is None or not owns(claims, subscription, "user_id") or not await watchr_core.delete_subscription(subscription_id):
        return _not_found("Subscription")
    return ok(message="Subscription deleted successfully")
