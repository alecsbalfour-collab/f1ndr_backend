# f1ndr-backend/watchr/db/event_log_repo.py
"""
Event log repository.
"""

class EventLogRepo:
    def __init__(self, client):
        self.collection = client["watchr_event_log"]

    async def insert(self, doc: dict):
        await self.collection.insert_one(doc)

    async def fetch(self, query: dict):
        cursor = self.collection.find(query)
        return [d async for d in cursor]
