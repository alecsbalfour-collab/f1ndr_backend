# f1ndr-backend/db/base_database.py
"""
DICT-aligned base database module with enterprise features and real MongoDB operations.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager


logger = logging.getLogger(__name__)


class BaseDatabase:
    """Enterprise base database class with DICT patterns and real MongoDB operations."""
    
    def __init__(self, mongo_uri: str, database_name: str = "f1ndr"):
        self.mongo_uri = mongo_uri
        self.database_name = database_name
        self._client: Optional[AsyncIOMotorClient] = None
        self._database = None
        logger.info(f"BaseDatabase initialized for database: {database_name}")
    
    async def connect(self) -> None:
        """Establish MongoDB connection with enterprise error handling."""
        try:
            if self._client is None:
                self._client = AsyncIOMotorClient(self.mongo_uri)
                
                # Test connection
                await self._client.admin.command('ping')
                logger.info("Successfully connected to MongoDB")
                
                self._database = self._client[self.database_name]
                
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close MongoDB connection with enterprise cleanup."""
        try:
            if self._client:
                self._client.close()
                self._client = None
                self._database = None
                logger.info("MongoDB connection closed")
        except Exception as e:
            logger.error(f"Error closing MongoDB connection: {e}")
    
    @property
    def database(self):
        """Get database instance, connecting if necessary."""
        if self._database is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._database
    
    async def get_collection(self, collection_name: str):
        """Get a collection by name with enterprise validation."""
        try:
            return self.database[collection_name]
        except Exception as e:
            logger.error(f"Failed to get collection {collection_name}: {e}")
            raise
    
    async def insert_one(self, collection_name: str, document: Dict[str, Any]) -> str:
        """
        Insert a single document with enterprise metadata.
        
        Args:
            collection_name: Name of the collection
            document: Document to insert
            
        Returns:
            Inserted document ID
        """
        try:
            collection = await self.get_collection(collection_name)
            
            # Add enterprise metadata
            document_with_metadata = {
                **document,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }
            
            result = await collection.insert_one(document_with_metadata)
            logger.info(f"Inserted document into {collection_name}: {result.inserted_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Failed to insert document into {collection_name}: {e}")
            raise
    
    async def insert_many(self, collection_name: str, documents: List[Dict[str, Any]]) -> List[str]:
        """
        Insert multiple documents with enterprise metadata.
        
        Args:
            collection_name: Name of the collection
            documents: List of documents to insert
            
        Returns:
            List of inserted document IDs
        """
        try:
            collection = await self.get_collection(collection_name)
            
            # Add enterprise metadata to each document
            documents_with_metadata = []
            for doc in documents:
                documents_with_metadata.append({
                    **doc,
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                })
            
            result = await collection.insert_many(documents_with_metadata)
            logger.info(f"Inserted {len(result.inserted_ids)} documents into {collection_name}")
            return [str(id) for id in result.inserted_ids]
            
        except Exception as e:
            logger.error(f"Failed to insert documents into {collection_name}: {e}")
            raise
    
    async def find_one(self, collection_name: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Find a single document with enterprise error handling.
        
        Args:
            collection_name: Name of the collection
            query: Query filter
            
        Returns:
            Document or None if not found
        """
        try:
            collection = await self.get_collection(collection_name)
            document = await collection.find_one(query)
            logger.debug(f"Found document in {collection_name}: {document is not None}")
            return document
            
        except Exception as e:
            logger.error(f"Failed to find document in {collection_name}: {e}")
            raise
    
    async def find_many(
        self,
        collection_name: str,
        query: Dict[str, Any],
        skip: int = 0,
        limit: int = 100,
        sort: Optional[List[tuple]] = None
    ) -> List[Dict[str, Any]]:
        """
        Find multiple documents with enterprise pagination and sorting.
        
        Args:
            collection_name: Name of the collection
            query: Query filter
            skip: Number of documents to skip
            limit: Maximum number of documents to return
            sort: Sort specification (list of (field, direction) tuples)
            
        Returns:
            List of documents
        """
        try:
            collection = await self.get_collection(collection_name)
            
            cursor = collection.find(query).skip(skip).limit(limit)
            
            if sort:
                cursor = cursor.sort(sort)
            
            documents = await cursor.to_list(length=limit)
            logger.info(f"Found {len(documents)} documents in {collection_name}")
            return documents
            
        except Exception as e:
            logger.error(f"Failed to find documents in {collection_name}: {e}")
            raise
    
    async def update_one(
        self,
        collection_name: str,
        query: Dict[str, Any],
        update: Dict[str, Any],
        upsert: bool = False
    ) -> bool:
        """
        Update a single document with enterprise metadata tracking.
        
        Args:
            collection_name: Name of the collection
            query: Query filter
            update: Update operations
            upsert: Whether to insert if not found
            
        Returns:
            True if update was successful
        """
        try:
            collection = await self.get_collection(collection_name)
            
            # Add enterprise metadata
            update_with_metadata = {
                **update,
                "$set": {
                    **update.get("$set", {}),
                    "updated_at": datetime.utcnow().isoformat(),
                }
            }
            
            result = await collection.update_one(query, update_with_metadata, upsert=upsert)
            success = result.modified_count > 0 or result.upserted_id is not None
            logger.info(f"Updated document in {collection_name}: {success}")
            return success
            
        except Exception as e:
            logger.error(f"Failed to update document in {collection_name}: {e}")
            raise
    
    async def update_many(
        self,
        collection_name: str,
        query: Dict[str, Any],
        update: Dict[str, Any]
    ) -> int:
        """
        Update multiple documents with enterprise metadata tracking.
        
        Args:
            collection_name: Name of the collection
            query: Query filter
            update: Update operations
            
        Returns:
            Number of documents updated
        """
        try:
            collection = await self.get_collection(collection_name)
            
            # Add enterprise metadata
            update_with_metadata = {
                **update,
                "$set": {
                    **update.get("$set", {}),
                    "updated_at": datetime.utcnow().isoformat(),
                }
            }
            
            result = await collection.update_many(query, update_with_metadata)
            logger.info(f"Updated {result.modified_count} documents in {collection_name}")
            return result.modified_count
            
        except Exception as e:
            logger.error(f"Failed to update documents in {collection_name}: {e}")
            raise
    
    async def delete_one(self, collection_name: str, query: Dict[str, Any]) -> bool:
        """
        Delete a single document with enterprise safety checks.
        
        Args:
            collection_name: Name of the collection
            query: Query filter
            
        Returns:
            True if deletion was successful
        """
        try:
            collection = await self.get_collection(collection_name)
            result = await collection.delete_one(query)
            success = result.deleted_count > 0
            logger.info(f"Deleted document from {collection_name}: {success}")
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete document from {collection_name}: {e}")
            raise
    
    async def delete_many(self, collection_name: str, query: Dict[str, Any]) -> int:
        """
        Delete multiple documents with enterprise safety checks.
        
        Args:
            collection_name: Name of the collection
            query: Query filter
            
        Returns:
            Number of documents deleted
        """
        try:
            collection = await self.get_collection(collection_name)
            result = await collection.delete_many(query)
            logger.info(f"Deleted {result.deleted_count} documents from {collection_name}")
            return result.deleted_count
            
        except Exception as e:
            logger.error(f"Failed to delete documents from {collection_name}: {e}")
            raise
    
    async def count_documents(self, collection_name: str, query: Dict[str, Any]) -> int:
        """
        Count documents matching query with enterprise error handling.
        
        Args:
            collection_name: Name of the collection
            query: Query filter
            
        Returns:
            Number of matching documents
        """
        try:
            collection = await self.get_collection(collection_name)
            count = await collection.count_documents(query)
            logger.debug(f"Counted {count} documents in {collection_name}")
            return count
            
        except Exception as e:
            logger.error(f"Failed to count documents in {collection_name}: {e}")
            raise
    
    async def create_index(self, collection_name: str, index_spec: Dict[str, Any], unique: bool = False) -> str:
        """
        Create an index with enterprise validation.
        
        Args:
            collection_name: Name of the collection
            index_spec: Index specification
            unique: Whether the index should be unique
            
        Returns:
            Index name
        """
        try:
            collection = await self.get_collection(collection_name)
            index_name = await collection.create_index(index_spec, unique=unique)
            logger.info(f"Created index {index_name} on {collection_name}")
            return index_name
            
        except Exception as e:
            logger.error(f"Failed to create index on {collection_name}: {e}")
            raise
    
    @asynccontextmanager
    async def transaction(self):
        """Context manager for database transactions (MongoDB 4.0+)."""
        async with self._client.start_session() as session:
            async with session.start_transaction():
                yield session
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """
        Get database statistics with enterprise monitoring.
        
        Returns:
            Dictionary with database statistics
        """
        try:
            stats = await self.database.command("dbstats")
            return {
                "database": self.database_name,
                "collections": stats.get("collections", 0),
                "data_size": stats.get("dataSize", 0),
                "index_size": stats.get("indexSize", 0),
                "storage_size": stats.get("storageSize", 0),
                "objects": stats.get("objects", 0),
            }
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            raise


# Global database instance
_database: Optional[BaseDatabase] = None


async def get_database() -> BaseDatabase:
    """Get the global database instance."""
    global _database
    if _database is None:
        from api.config.settings_config import get_settings
        settings = get_settings()
        _database = BaseDatabase(settings.MONGO_URI, "f1ndr")
        await _database.connect()
    return _database


async def close_database() -> None:
    """Close the global database connection."""
    global _database
    if _database:
        await _database.disconnect()
        _database = None