"""
listr module entrypoint.
"""

from listr.core.core import push_listing, update_listing, remove_listing


async def run(action: str, data: dict) -> dict:
    if action == "push":
        return await push_listing(data.get("platform"), data)
    if action == "update":
        return await update_listing(data.get("platform"), data)
    if action == "remove":
        return await remove_listing(data.get("platform"), data)
    raise ValueError(f"Invalid listr action: {action}")
