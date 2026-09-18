# f1ndr-backend/trinn/data/normalize_data.py
"""
DICT-aligned TRINN normalize data builders with enterprise features.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class NormalizePayload:
    """Enterprise normalize payload with DICT patterns."""
    id: Optional[str] = None
    title: Optional[str] = None
    price: Optional[float] = None
    location: Optional[str] = None
    source: Optional[str] = None
    normalized_at: str = None
    processing_version: str = "1.0.0"
    field_mapping: Dict[str, str] = None
    
    def __post_init__(self):
        if self.normalized_at is None:
            self.normalized_at = datetime.utcnow().isoformat()
        if self.field_mapping is None:
            self.field_mapping = {}


def build_normalize_payload(enriched: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build normalize payload with enterprise metadata.
    
    Args:
        enriched: Enriched data to normalize
        
    Returns:
        Dictionary with normalized data and metadata
    """
    try:
        base = enriched.get("raw", {})
        
        payload = NormalizePayload(
            id=base.get("id"),
            title=base.get("title"),
            price=_safe_float(base.get("price")),
            location=base.get("location"),
            source=enriched.get("source"),
        )
        
        result = {
            "id": payload.id,
            "title": payload.title,
            "price": payload.price,
            "location": payload.location,
            "source": payload.source,
            "normalized_at": payload.normalized_at,
            "processing_version": payload.processing_version,
            "field_mapping": payload.field_mapping,
        }
        
        logger.debug(f"Built normalize payload for ID: {payload.id}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to build normalize payload: {e}")
        raise


def build_normalize_metadata(enriched: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build normalization metadata with enterprise tracking.
    
    Args:
        enriched: Enriched data to extract metadata from
        
    Returns:
        Dictionary with normalization metadata
    """
    base = enriched.get("raw", {})
    
    metadata = {
        "timestamp": datetime.utcnow().isoformat(),
        "processing_stage": "normalize",
        "original_field_count": len(base.keys()),
        "normalized_field_count": 0,
        "fields_normalized": [],
    }
    
    # Track which fields were normalized
    normalize_fields = ["title", "description", "location"]
    for field in normalize_fields:
        if field in base:
            metadata["fields_normalized"].append(field)
            metadata["normalized_field_count"] += 1
    
    return metadata


def _safe_float(value: Any) -> Optional[float]:
    """Safely convert value to float."""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None
