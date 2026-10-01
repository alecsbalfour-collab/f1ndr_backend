# api/auth/audit.py
"""Append-only audit trail: who did what, when, from where."""

import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import Request

from api.auth import store

logger = logging.getLogger("api.audit")


async def record_audit(
    event: str,
    request: Optional[Request] = None,
    *,
    user_id: Optional[str] = None,
    actor_id: Optional[str] = None,
    email: Optional[str] = None,
    success: bool = True,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """`user_id` is the account affected; `actor_id` who acted (defaults to the same). Never raises."""
    entry = {
        "id": str(uuid.uuid4()),
        "event": event,
        "success": success,
        "user_id": user_id,
        "actor_id": actor_id or user_id,
        "email": email,
        "details": details or {},
        "created_at": store.utcnow(),
    }
    if request is not None:
        entry.update(
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            request_id=getattr(request.state, "request_id", None),
            path=request.url.path,
        )
    try:
        await store.audit_log.upsert(entry)
    except Exception:
        logger.exception("Failed to write audit event %s", event)
        return
    logger.info("audit event=%s success=%s user_id=%s actor_id=%s", event, success, user_id, entry["actor_id"])


async def list_audit(query: Dict[str, Any], skip: int = 0, limit: int = 50) -> List[dict]:
    entries = await store.audit_log.find(query, skip=skip, limit=limit, sort=("created_at", -1))
    return [{**e, "created_at": e["created_at"].isoformat() + "Z"} for e in entries]
