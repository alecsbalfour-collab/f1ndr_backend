# f1ndr-backend/watchr/db/mongo_client_watchr.py
"""
Mongo client for Watchr.
"""

from motor.motor_asyncio import AsyncIOMotorClient


def get_watchr_client(uri: str):
    return AsyncIOMotorClient(uri)
