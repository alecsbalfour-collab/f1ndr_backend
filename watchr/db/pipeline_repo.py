# f1ndr-backend/watchr/db/pipeline_repo.py
"""
Pipeline repository for Watchr.
"""

class PipelineRepo:
    def __init__(self, client):
        self.collection = client["watchr_pipeline"]

    async def insert(self, doc: dict):
        await self.collection.insert_one(doc)

    async def process_stage(self, payload: dict) -> dict:
        await self.collection.insert_one(payload)
        return payload
