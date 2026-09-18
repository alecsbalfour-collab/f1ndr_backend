# f1ndr-backend/trinn/db/mongo_client_trinn.py
"""
DICT-aligned TRINN MongoDB client with enterprise features.
"""

import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient


logger = logging.getLogger(__name__)


class TrinnMongoClient:
    """Enterprise MongoDB client with DICT patterns."""
    
    def __init__(self, uri: str, database_name: str = "f1ndr"):
        self.uri = uri
        self.database_name = database_name
        self._client: Optional[AsyncIOMotorClient] = None
        logger.info(f"TrinnMongoClient initialized for database: {database_name}")
    
    async def connect(self) -> AsyncIOMotorClient:
        """
        Establish MongoDB connection with enterprise error handling.
        
        Returns:
            AsyncIOMotorClient instance
        """
        try:
            if self._client is None:
                self._client = AsyncIOMotorClient(self.uri)
                
                # Test connection
                await self._client.admin.command('ping')
                logger.info("Successfully connected to MongoDB")
                
            return self._client
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close MongoDB connection with enterprise cleanup."""
        try:
            if self._client:
                self._client.close()
                self._client = None
                logger.info("MongoDB connection closed")
        except Exception as e:
            logger.error(f"Error closing MongoDB connection: {e}")
    
    async def get_database(self):
        """
        Get database instance with enterprise validation.
        
        Returns:
            MongoDB database instance
        """
        client = await self.connect()
        return client[self.database_name]
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()


def get_trinn_client(uri: str, database_name: str = "f1ndr") -> TrinnMongoClient:
    """
    Get TRINN MongoDB client instance with enterprise configuration.
    
    Args:
        uri: MongoDB connection URI
        database_name: Database name
        
    Returns:
        TrinnMongoClient instance
    """
    return TrinnMongoClient(uri, database_name)
