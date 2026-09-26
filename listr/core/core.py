"""
Core marketplace posting logic for listr.
"""

from datetime import datetime

from listr.config.config import get_listr_config
from listr.db.listing_repo import save_listing, update_listing_db, remove_listing_db
from listr.utils.listing_utils import truncate_title


def _prepare(platform: str, listing: dict) -> tuple:
    config = get_listr_config()
    if platform not in config["supported_platforms"]:
        raise ValueError(f"Unsupported listr platform: {platform}")
    prepared = {**listing, "platform": platform, "updated_at": datetime.utcnow().isoformat()}
    if prepared.get("title"):
        prepared["title"] = truncate_title(prepared["title"], config["max_title_length"])
    return config, prepared


def push_listing(platform: str, listing: dict) -> dict:
    _, prepared = _prepare(platform, listing)
    save_listing(platform, prepared)
    return {"platform": platform, "status": "pushed", "listing": prepared}


def update_listing(platform: str, listing: dict) -> dict:
    _, prepared = _prepare(platform, listing)
    updated = update_listing_db(platform, prepared)
    return {"platform": platform, "status": "updated" if updated else "created", "listing": prepared}


def remove_listing(platform: str, listing: dict) -> dict:
    _, prepared = _prepare(platform, listing)
    removed = remove_listing_db(platform, prepared)
    return {"platform": platform, "status": "removed" if removed else "not_found", "listing_id": prepared.get("id")}
