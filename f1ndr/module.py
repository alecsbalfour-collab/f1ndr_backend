"""
f1ndr module entrypoint.
"""

from f1ndr.core.core import run_search, run_intelligence


async def run(action: str, data: dict) -> dict:
    if action == "search":
        return await run_search(data)
    if action == "intelligence":
        return await run_intelligence(data)
    raise ValueError(f"Invalid f1ndr action: {action}")
