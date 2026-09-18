# f1ndr-backend/watchr/db/watcher_state_repo.py
"""
Watcher state repository.
"""

class WatcherStateRepo:
    def __init__(self, client):
        self.collection = client["watchr_state"]

    async def insert(self, doc: dict):
        await self.collection.insert_one(doc)

    async def fetch(self, query: dict):
        cursor = self.collection.find(query)
        return [d async for d in cursor]
