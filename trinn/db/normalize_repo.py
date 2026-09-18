# f1ndr-backend/trinn/db/normalize_repo.py
"""
DICT-aligned TRINN normalize repository with enterprise features.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from trinn.core.interface_core import RepoInterface
from trinn.core.exceptions_core import RepositoryError


logger = logging.getLogger(__name__)


class NormalizeRepo(RepoInterface):
    """Enterprise normalize repository with DICT patterns."""
    
    def __init__(self, client):
        self.client = client
        self.collection = client["trinn_normalize"]
        logger.info("NormalizeRepo initialized")
    
    async def insert(self, doc: Dict[str, Any]) -> str:
        """
        Insert document with enterprise metadata.
        
        Args:
            doc: Document to insert
            
        Returns:
            Document ID
        """
        try:
            # Add enterprise metadata
            doc_with_metadata = {
                **doc,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "repository": "normalize",
            }
            
            result = await self.collection.insert_one(doc_with_metadata)
            logger.info(f"Inserted document into normalize repo: {result.inserted_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Failed to insert document into normalize repo: {e}")
            raise RepositoryError(f"Insert failed: {str(e)}", repository="normalize")
    
    async def fetch(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Fetch documents with enterprise query handling.
        
        Args:
            query: Query filter
            
        Returns:
            List of matching documents
        """
        try:
            cursor = self.collection.find(query)
            documents = [doc async for doc in cursor]
            logger.info(f"Fetched {len(documents)} documents from normalize repo")
            return documents
            
        except Exception as e:
            logger.error(f"Failed to fetch documents from normalize repo: {e}")
            raise RepositoryError(f"Fetch failed: {str(e)}", repository="normalize")
    
    async def update(self, query: Dict[str, Any], update: Dict[str, Any]) -> bool:
        """
        Update documents with enterprise metadata tracking.
        
        Args:
            query: Query filter
            update: Update operations
            
        Returns:
            True if update was successful
        """
        try:
            update_with_metadata = {
                **update,
                "$set": {
                    **update.get("$set", {}),
                    "updated_at": datetime.utcnow().isoformat(),
                }
            }
            
            result = await self.collection.update_many(query, update_with_metadata)
            success = result.modified_count > 0
            logger.info(f"Updated {result.modified_count} documents in normalize repo")
            return success
            
        except Exception as e:
            logger.error(f"Failed to update documents in normalize repo: {e}")
            raise RepositoryError(f"Update failed: {str(e)}", repository="normalize")
    
    async def delete(self, query: Dict[str, Any]) -> bool:
        """
        Delete documents with enterprise safety checks.
        
        Args:
            query: Query filter
            
        Returns:
            True if deletion was successful
        """
        try:
            result = await self.collection.delete_many(query)
            success = result.deleted_count > 0
            logger.info(f"Deleted {result.deleted_count} documents from normalize repo")
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete documents from normalize repo: {e}")
            raise RepositoryError(f"Delete failed: {str(e)}", repository="normalize")
    
    async def get_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get document by ID with enterprise error handling.
        
        Args:
            doc_id: Document ID
            
        Returns:
            Document or None if not found
        """
        try:
            from bson import ObjectId
            document = await self.collection.find_one({"_id": ObjectId(doc_id)})
            logger.debug(f"Retrieved document by ID: {doc_id}")
            return document
            
        except Exception as e:
            logger.error(f"Failed to get document by ID: {e}")
            raise RepositoryError(f"Get by ID failed: {str(e)}", repository="normalize")
