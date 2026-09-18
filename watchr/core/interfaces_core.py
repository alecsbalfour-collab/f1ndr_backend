# f1ndr-backend/watchr/core/interfaces_core.py
"""
Watchr interface definitions.
"""

class RepoInterface:
    async def insert(self, doc: dict):
        raise NotImplementedError

    async def fetch(self, query: dict):
        raise NotImplementedError
