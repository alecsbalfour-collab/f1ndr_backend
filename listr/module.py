"""
listr module entrypoint.
"""

from listr.core.core import push_listing, update_listing, remove_listing


async def run(action: str, data: dict) -> dict:
    if action == "push":
        return push_listing(data.get("platform"), data)
    if action == "update":
        return update_listing(data.get("platform"), data)
    if action == "remove":
        return remove_listing(data.get("platform"), data)
    raise ValueError(f"Invalid listr action: {action}")
