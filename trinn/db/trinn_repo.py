# f1ndr-backend/trinn/db/trinn_repo.py
"""
DICT-aligned TRINN task repository with enterprise features.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass
import uuid


logger = logging.getLogger(__name__)


@dataclass
class TaskRepository:
    """Enterprise task repository with DICT patterns."""
    
    def __init__(self, client):
        self.client = client
        self.collection = client["trinn_tasks"]
        logger.info("TaskRepository initialized")
    
    async def insert(self, task: Dict[str, Any]) -> str:
        """
        Insert a new task with enterprise metadata.
        
        Args:
            task: Task data to insert
            
        Returns:
            Task ID of the inserted task
        """
        try:
            # Generate task ID if not provided
            task_id = task.get("task_id") or str(uuid.uuid4())
            
            # Add enterprise metadata
            task_with_metadata = {
                **task,
                "task_id": task_id,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "status": "pending",
                "attempts": 0,
            }
            
            await self.collection.insert_one(task_with_metadata)
            logger.info(f"Task inserted with ID: {task_id}")
            return task_id
            
        except Exception as e:
            logger.error(f"Failed to insert task: {e}")
            raise
    
    async def fetch(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Fetch tasks matching the query.
        
        Args:
            query: MongoDB query filter
            
        Returns:
            List of matching tasks
        """
        try:
            cursor = self.collection.find(query)
            tasks = [task async for task in cursor]
            logger.info(f"Fetched {len(tasks)} tasks matching query")
            return tasks
            
        except Exception as e:
            logger.error(f"Failed to fetch tasks: {e}")
            raise
    
    async def update_task_status(self, task_id: str, status: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update task status with enterprise tracking.
        
        Args:
            task_id: Task ID to update
            status: New status value
            metadata: Optional metadata to include in update
            
        Returns:
            True if update was successful
        """
        try:
            update_data = {
                "status": status,
                "updated_at": datetime.utcnow().isoformat(),
            }
            
            if metadata:
                update_data.update(metadata)
            
            result = await self.collection.update_one(
                {"task_id": task_id},
                {"$set": update_data}
            )
            
            success = result.modified_count > 0
            logger.info(f"Task {task_id} status updated to {status}: {success}")
            return success
            
        except Exception as e:
            logger.error(f"Failed to update task status: {e}")
            raise
    
    async def increment_attempts(self, task_id: str) -> bool:
        """
        Increment task attempt counter.
        
        Args:
            task_id: Task ID to update
            
        Returns:
            True if update was successful
        """
        try:
            result = await self.collection.update_one(
                {"task_id": task_id},
                {
                    "$inc": {"attempts": 1},
                    "$set": {"updated_at": datetime.utcnow().isoformat()}
                }
            )
            
            success = result.modified_count > 0
            logger.info(f"Task {task_id} attempts incremented: {success}")
            return success
            
        except Exception as e:
            logger.error(f"Failed to increment task attempts: {e}")
            raise
    
    async def get_pending_tasks(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get pending tasks scheduled for execution.
        
        Args:
            limit: Maximum number of tasks to return
            
        Returns:
            List of pending tasks
        """
        try:
            cursor = self.collection.find(
                {"status": "pending"}
            ).sort("created_at", 1).limit(limit)
            
            tasks = [task async for task in cursor]
            logger.info(f"Retrieved {len(tasks)} pending tasks")
            return tasks
            
        except Exception as e:
            logger.error(f"Failed to get pending tasks: {e}")
            raise
    
    async def delete_task(self, task_id: str) -> bool:
        """
        Delete a task from the repository.
        
        Args:
            task_id: Task ID to delete
            
        Returns:
            True if deletion was successful
        """
        try:
            result = await self.collection.delete_one({"task_id": task_id})
            success = result.deleted_count > 0
            logger.info(f"Task {task_id} deleted: {success}")
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete task: {e}")
            raise


# Global repository instance (will be initialized with client)
_task_repo: Optional[TaskRepository] = None


def initialize_task_repo(client) -> TaskRepository:
    """Initialize the global task repository instance."""
    global _task_repo
    _task_repo = TaskRepository(client)
    return _task_repo


def reset_task_repo() -> None:
    """Detach the task repository (e.g. on shutdown)."""
    global _task_repo
    _task_repo = None


def get_task_repo() -> TaskRepository:
    """Get the global task repository instance."""
    if _task_repo is None:
        raise RuntimeError("Task repository not initialized. Call initialize_task_repo first.")
    return _task_repo


# Legacy functions for backward compatibility
def save_task(task: Dict[str, Any]) -> str:
    """Legacy function to save task (deprecated, use repository directly)."""
    logger.warning("save_task is deprecated, use TaskRepository.insert instead")
    if _task_repo is None:
        raise RuntimeError("Task repository not initialized")
    
    # For backward compatibility, this is a synchronous wrapper
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(_task_repo.insert(task))


def update_task_status(task_id: str, status: str) -> bool:
    """Legacy function to update task status (deprecated, use repository directly)."""
    logger.warning("update_task_status is deprecated, use TaskRepository.update_task_status instead")
    if _task_repo is None:
        raise RuntimeError("Task repository not initialized")
    
    # For backward compatibility, this is a synchronous wrapper
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(_task_repo.update_task_status(task_id, status))
