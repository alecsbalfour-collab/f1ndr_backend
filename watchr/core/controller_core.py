# f1ndr-backend/watchr/core/controller_core.py
"""
Watchr controller layer.
"""

from watchr.core.service_core import WatchrService


class WatchrController:
    def __init__(self, service: WatchrService):
        self.service = service

    async def process(self, payload: dict) -> dict:
        return await self.service.process(payload)
