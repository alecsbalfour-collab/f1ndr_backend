"""
dealr module entrypoint.
"""

from dealr.core.core import ingest_inventory, sync_inventory


def run(action: str, data: dict):
    if action == "ingest":
        return ingest_inventory(data)
    if action == "sync":
        return sync_inventory(data)
    raise ValueError("Invalid dealr action")
