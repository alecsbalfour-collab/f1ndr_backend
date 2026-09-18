# f1ndr-backend/trinn/utils/enrich_utils.py
"""
DICT-aligned TRINN enrich utilities with enterprise features.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime


logger = logging.getLogger(__name__)


def enrich_with_metadata(data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Enrich data with enterprise metadata.
    
    Args:
        data: Base data to enrich
        metadata: Optional metadata to add
        
    Returns:
        Enriched data dictionary
    """
    enriched = data.copy()
    
    # Add enterprise metadata
    enriched["enrichment_metadata"] = {
        "enriched_at": datetime.utcnow().isoformat(),
        "enrichment_version": "1.0.0",
        "original_field_count": len(data.keys()),
    }
    
    # Add custom metadata if provided
    if metadata:
        enriched["enrichment_metadata"].update(metadata)
    
    logger.debug(f"Enriched data with metadata: {len(data)} -> {len(enriched)} fields")
    return enriched


def enrich_with_source_tracking(data: Dict[str, Any], source: Optional[str] = None) -> Dict[str, Any]:
    """
    Enrich data with source tracking information.
    
    Args:
        data: Base data to enrich
        source: Source identifier
        
    Returns:
        Enriched data with source tracking
    """
    enriched = data.copy()
    
    # Add source tracking
    enriched["source_tracking"] = {
        "source": source or enriched.get("source", "unknown"),
        "source_received_at": datetime.utcnow().isoformat(),
        "source_confidence": 1.0,  # Default confidence
    }
    
    logger.debug(f"Enriched data with source tracking: {source}")
    return enriched


def enrich_with_data_quality_metrics(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich data with enterprise data quality metrics.
    
    Args:
        data: Base data to analyze
        
    Returns:
        Enriched data with quality metrics
    """
    quality_metrics = {
        "completeness": _calculate_completeness(data),
        "field_count": len(data.keys()),
        "empty_fields": _count_empty_fields(data),
        "data_size_bytes": len(str(data)),
        "analyzed_at": datetime.utcnow().isoformat(),
    }
    
    enriched = data.copy()
    enriched["data_quality"] = quality_metrics
    
    logger.debug(f"Enriched data with quality metrics: completeness={quality_metrics['completeness']:.2f}")
    return enriched


def _calculate_completeness(data: Dict[str, Any]) -> float:
    """Calculate data completeness percentage."""
    if not data:
        return 0.0
    
    non_empty_fields = sum(1 for value in data.values() if value is not None and value != "")
    total_fields = len(data)
    
    return (non_empty_fields / total_fields) * 100 if total_fields > 0 else 0.0


def _count_empty_fields(data: Dict[str, Any]) -> int:
    """Count empty or null fields in data."""
    return sum(1 for value in data.values() if value is None or value == "")


def enrich_with_timestamps(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich data with enterprise timestamp tracking.
    
    Args:
        data: Base data to enrich
        
    Returns:
        Enriched data with timestamps
    """
    enriched = data.copy()
    
    enriched["timestamp_tracking"] = {
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "processing_stage": "enrich",
    }
    
    logger.debug("Enriched data with timestamp tracking")
    return enriched


def batch_enrich(data_list: List[Dict[str, Any]], enrich_functions: List[Callable]) -> List[Dict[str, Any]]:
    """
    Batch enrich multiple data items with enterprise efficiency.
    
    Args:
        data_list: List of data items to enrich
        enrich_functions: List of enrichment functions to apply
        
    Returns:
        List of enriched data items
    """
    enriched_list = []
    
    for data in data_list:
        enriched = data.copy()
        
        for enrich_func in enrich_functions:
            try:
                enriched = enrich_func(enriched)
            except Exception as e:
                logger.warning(f"Enrichment function failed: {e}")
                # Continue with other functions
        
        enriched_list.append(enriched)
    
    logger.info(f"Batch enriched {len(data_list)} items with {len(enrich_functions)} functions")
    return enriched_list
