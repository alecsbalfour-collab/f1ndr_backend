"""
sellr module entrypoint.
"""

from sellr.core.core import create_listing


def run(data: dict) -> dict:
    return create_listing(data)
