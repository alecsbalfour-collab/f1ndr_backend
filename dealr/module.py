"""
dealr module entrypoint.
"""

from dealr.core.core import ingest_inventory, sync_inventory


async def run(action: str, data: dict) -> dict:
    if action == "ingest":
        return ingest_inventory(data)
    if action == "sync":
        return await sync_inventory(data)
    raise ValueError(f"Invalid dealr action: {action}")
