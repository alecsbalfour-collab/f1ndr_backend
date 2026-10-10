"""Send-to-phone photo sessions for listing drafts.

A session is a short-lived upload capability: the owner creates it from a
logged-in device, then opens `phone_url` on a phone (token in the path, no
login) and uploads raw image bytes. Unattached photos of expired sessions are
deleted; photos referenced by a created listing are marked attached and live on.
"""

import base64
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sellr.config.config import get_sellr_config
from sellr.db.photo_repo import photos_store, sessions_store


class PhotoError(Exception):
    """Business-rule failure mapped to an HTTP error by the route layer."""

    def __init__(self, message: str, status: int, code: str):
        super().__init__(message)
        self.status = status
        self.code = code


def _utcnow() -> datetime:
    return datetime.utcnow()


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _sniff(content_type: str, data: bytes) -> Optional[str]:
    """Declared content-type must match the magic bytes; returns the normalized type."""
    ct = content_type.split(";")[0].strip().lower()
    if ct == "image/jpeg" and data.startswith(b"\xff\xd8\xff"):
        return ct
    if ct == "image/png" and data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ct
    if ct == "image/webp" and len(data) > 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ct
    if ct in ("image/heic", "image/heif") and len(data) > 16 and data[4:8] == b"ftyp":
        if any(brand in data[8:16] for brand in (b"heic", b"heix", b"hevc", b"hevx", b"mif1")):
            return ct
    return None


def _is_expired(session: dict) -> bool:
    return session["status"] == "open" and session["expires_at_dt"] <= _utcnow()


async def _mark_expired(session: dict) -> bool:
    """Expiry is checked on access so in-memory and Mongo behave identically."""
    if not _is_expired(session):
        return False
    session["status"] = "expired"
    await sessions_store.update(session["id"], {"status": "expired"})
    for photo_id in session["photos"]:
        photo = await photos_store.get(photo_id)
        if photo and not photo.get("attached"):
            await photos_store.delete(photo_id)
    return True


async def _session_by_token(token: str) -> Optional[dict]:
    sessions = await sessions_store.find({"token_hash": _token_hash(token)}, limit=1)
    if not sessions:
        return None
    session = sessions[0]
    await _mark_expired(session)
    return session


def phone_url(token: str) -> str:
    base = get_sellr_config()["phone_upload_base_url"].rstrip("/")
    return f"{base}/api/v1/sellr/photo-upload/{token}"


def photo_meta(photo: dict) -> dict:
    return {
        "id": photo["id"],
        "content_type": photo["content_type"],
        "size": photo["size"],
        "created_at": photo["created_at"],
        "url": f"/api/v1/sellr/photos/{photo['id']}",
    }


def photo_content(photo: dict) -> dict:
    return {
        "id": photo["id"],
        "content_type": photo["content_type"],
        "size": photo["size"],
        "data_b64": base64.b64encode(photo["data"]).decode(),
    }


async def public_session(session: dict) -> dict:
    photos = []
    for photo_id in session["photos"]:
        photo = await photos_store.get(photo_id)
        if photo:
            photos.append(photo_meta(photo))
    return {
        "id": session["id"],
        "status": session["status"],
        "photos": photos,
        "listing_id": session.get("listing_id"),
        "created_at": session["created_at"],
        "expires_at": session["expires_at"],
    }


async def _sweep_owner_sessions(owner_id: str) -> None:
    for session in await sessions_store.find({"owner_id": owner_id}, limit=100):
        await _mark_expired(session)


async def create_session(owner_id: str, listing_id: Optional[str] = None) -> Tuple[dict, str]:
    await _sweep_owner_sessions(owner_id)
    config = get_sellr_config()
    expires = _utcnow() + timedelta(minutes=config["photo_session_ttl_minutes"])
    token = secrets.token_urlsafe(32)
    session = {
        "id": str(uuid.uuid4()),
        "owner_id": owner_id,
        "token_hash": _token_hash(token),
        "status": "open",
        "photos": [],
        "listing_id": listing_id,
        "created_at": _utcnow().isoformat(),
        "expires_at": expires.isoformat(),
        "expires_at_dt": expires,
    }
    await sessions_store.upsert(session)
    return session, token


async def fetch_session(session_id: str) -> Optional[dict]:
    session = await sessions_store.get(session_id)
    if session:
        await _mark_expired(session)
    return session


async def close_session(session: dict) -> dict:
    if session["status"] == "open":
        await sessions_store.update(session["id"], {"status": "closed"})
        session["status"] = "closed"
    return session


async def token_session_alive(token: str) -> bool:
    """The phone upload page distinguishes dead links before accepting files."""
    session = await _session_by_token(token)
    return session is not None and session["status"] == "open"


async def upload_by_token(token: str, data: bytes, content_type: str) -> dict:
    config = get_sellr_config()
    session = await _session_by_token(token)
    if session is None:
        raise PhotoError("Photo session not found", 404, "NOT_FOUND")
    if session["status"] == "expired":
        raise PhotoError("Photo session has expired", 410, "SESSION_EXPIRED")
    if session["status"] != "open":
        raise PhotoError("Photo session is closed", 409, "SESSION_CLOSED")
    if len(session["photos"]) >= config["photo_session_max_photos"]:
        raise PhotoError("Photo session is full", 409, "SESSION_FULL")
    if not data:
        raise PhotoError("Empty upload body", 400, "EMPTY_BODY")
    if len(data) > config["photo_max_bytes"]:
        raise PhotoError("Photo exceeds the size limit", 413, "PHOTO_TOO_LARGE")
    sniffed = _sniff(content_type, data)
    if sniffed is None:
        raise PhotoError("Unsupported or mismatched image type", 415, "UNSUPPORTED_MEDIA")

    photo = {
        "id": str(uuid.uuid4()),
        "session_id": session["id"],
        "owner_id": session["owner_id"],
        "content_type": sniffed,
        "size": len(data),
        "data": data,
        "attached": False,
        "created_at": _utcnow().isoformat(),
    }
    await photos_store.upsert(photo)
    session["photos"] = session["photos"] + [photo["id"]]
    await sessions_store.update(session["id"], {"photos": session["photos"]})
    return photo_meta(photo)


async def fetch_photo(photo_id: str) -> Optional[dict]:
    return await photos_store.get(photo_id)


async def attach_photos(owner_id: str, photo_ids: List[str]) -> List[str]:
    """Validate that the caller owns every referenced photo, then mark them attached."""
    if not isinstance(photo_ids, list) or not all(isinstance(p, str) for p in photo_ids):
        raise PhotoError("photos must be a list of photo ids", 400, "INVALID_PHOTOS")
    for photo_id in photo_ids:
        photo = await photos_store.get(photo_id)
        if photo is None or photo["owner_id"] != owner_id:
            raise PhotoError("Unknown photo reference", 400, "INVALID_PHOTOS")
        if not photo.get("attached"):
            await photos_store.update(photo_id, {"attached": True})
    return photo_ids
