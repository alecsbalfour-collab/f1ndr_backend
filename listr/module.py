"""
listr module entrypoint.
"""

from listr.core.core import push_listing, update_listing, remove_listing


def run(action: str, data: dict):
    if action == "push":
        return push_listing(data.get("platform"), data)
    if action == "update":
        return update_listing(data.get("platform"), data)
    if action == "remove":
        return remove_listing(data.get("platform"), data)
    raise ValueError("Invalid listr action")
