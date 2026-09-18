# f1ndr-backend/trinn/core/interface_core.py
"""
DICT-aligned TRINN interface definitions with enterprise features.
"""

import logging
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod


logger = logging.getLogger(__name__)


class RepoInterface(ABC):
    """Enterprise repository interface with DICT patterns."""
    
    @abstractmethod
    async def insert(self, doc: Dict[str, Any]) -> str:
        """
        Insert a document into the repository.
        
        Args:
            doc: Document to insert
            
        Returns:
            Document ID
        """
        pass
    
    @abstractmethod
    async def fetch(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Fetch documents matching the query.
        
        Args:
            query: Query filter
            
        Returns:
            List of matching documents
        """
        pass
    
    @abstractmethod
    async def update(self, query: Dict[str, Any], update: Dict[str, Any]) -> bool:
        """
        Update documents matching the query.
        
        Args:
            query: Query filter
            update: Update operations
            
        Returns:
            True if update was successful
        """
        pass
    
    @abstractmethod
    async def delete(self, query: Dict[str, Any]) -> bool:
        """
        Delete documents matching the query.
        
        Args:
            query: Query filter
            
        Returns:
            True if deletion was successful
        """
        pass


class ServiceInterface(ABC):
    """Enterprise service interface with DICT patterns."""
    
    @abstractmethod
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process data with enterprise logic.
        
        Args:
            data: Input data to process
            
        Returns:
            Processed data with metadata
        """
        pass
    
    @abstractmethod
    async def get_metrics(self) -> Dict[str, Any]:
        """
        Get service metrics for monitoring.
        
        Returns:
            Dictionary with service metrics
        """
        pass


class SchedulerInterface(ABC):
    """Enterprise scheduler interface with DICT patterns."""
    
    @abstractmethod
    async def schedule_task(self, task_data: Dict[str, Any], interval_hours: int) -> str:
        """
        Schedule a task for execution.
        
        Args:
            task_data: Task data to schedule
            interval_hours: Interval between executions
            
        Returns:
            Task ID
        """
        pass
    
    @abstractmethod
    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a scheduled task.
        
        Args:
            task_id: Task ID to cancel
            
        Returns:
            True if cancellation was successful
        """
        pass
    
    @abstractmethod
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a scheduled task.
        
        Args:
            task_id: Task ID to query
            
        Returns:
            Task status dictionary or None
        """
        pass


class PipelineInterface(ABC):
    """Enterprise pipeline interface with DICT patterns."""
    
    @abstractmethod
    async def execute_pipeline(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the full pipeline with enterprise orchestration.
        
        Args:
            data: Input data for pipeline
            
        Returns:
            Pipeline execution results
        """
        pass
    
    @abstractmethod
    async def get_pipeline_status(self, pipeline_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a pipeline execution.
        
        Args:
            pipeline_id: Pipeline ID to query
            
        Returns:
            Pipeline status dictionary or None
        """
        pass
