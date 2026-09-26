"""
sellr module entrypoint.
"""

from sellr.core.core import create_listing
from sellr.utils.utils import update_listing, delete_listing, get_listing


async def run(action: str, data: dict) -> dict:
    if action == "create":
        return await create_listing(data)
    if action == "update":
        return {"updated": await update_listing(data["id"], data)}
    if action == "remove":
        return {"removed": await delete_listing(data["id"])}
    if action == "get":
        return {"listing": await get_listing(data["id"])}
    raise ValueError(f"Invalid sellr action: {action}")
