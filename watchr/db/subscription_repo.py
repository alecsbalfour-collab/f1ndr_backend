# f1ndr-backend/watchr/db/subscription_repo.py
"""
Subscription repository.
"""

class SubscriptionRepo:
    def __init__(self, client):
        self.collection = client["watchr_subscriptions"]

    async def insert(self, doc: dict):
        await self.collection.insert_one(doc)

    async def fetch(self, query: dict):
        cursor = self.collection.find(query)
        return [d async for d in cursor]
