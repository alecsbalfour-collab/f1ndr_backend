# f1ndr-backend/trinn/data/transform_data.py
"""
DICT-aligned TRINN transform data builders with enterprise features.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class TransformPayload:
    """Enterprise transform payload with DICT patterns."""
    id: Optional[str] = None
    title: Optional[str] = None
    price: Optional[float] = None
    location: Optional[str] = None
    canonical_source: Optional[str] = None
    transformed_at: str = None
    processing_version: str = "1.0.0"
    transformation_rules: Dict[str, str] = None
    
    def __post_init__(self):
        if self.transformed_at is None:
            self.transformed_at = datetime.utcnow().isoformat()
        if self.transformation_rules is None:
            self.transformation_rules = {}


def build_transform_payload(normalized: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build transform payload with enterprise metadata.
    
    Args:
        normalized: Normalized data to transform
        
    Returns:
        Dictionary with transformed data and metadata
    """
    try:
        from trinn.utils.transform_utils import map_source_to_canonical
        
        source = normalized.get("source")
        canonical_source = map_source_to_canonical(source)
        
        payload = TransformPayload(
            id=normalized.get("id"),
            title=normalized.get("title"),
            price=normalized.get("price"),
            location=normalized.get("location"),
            canonical_source=canonical_source,
        )
        
        result = {
            "id": payload.id,
            "title": payload.title,
            "price": payload.price,
            "location": payload.location,
            "canonical_source": payload.canonical_source,
            "transformed_at": payload.transformed_at,
            "processing_version": payload.processing_version,
            "transformation_rules": payload.transformation_rules,
        }
        
        logger.debug(f"Built transform payload for ID: {payload.id}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to build transform payload: {e}")
        raise


def build_transform_metadata(normalized: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build transformation metadata with enterprise tracking.
    
    Args:
        normalized: Normalized data to extract metadata from
        
    Returns:
        Dictionary with transformation metadata
    """
    source = normalized.get("source")
    
    metadata = {
        "timestamp": datetime.utcnow().isoformat(),
        "processing_stage": "transform",
        "original_source": source,
        "canonical_source": map_source_to_canonical(source),
        "transformations_applied": [],
    }
    
    # Track which transformations were applied
    if source and source != metadata["canonical_source"]:
        metadata["transformations_applied"].append("source_canonicalization")
    
    return metadata


def map_source_to_canonical(source: Optional[str]) -> str:
    """
    Map source to canonical format with enterprise validation.
    
    Args:
        source: Source string to canonicalize
        
    Returns:
        Canonical source string
    """
    if not source:
        return "unknown"
    
    # Apply canonicalization rules
    canonical = source.lower().strip()
    
    # Remove common prefixes/suffixes
    canonical = canonical.replace("www.", "")
    canonical = canonical.replace(".com", "")
    canonical = canonical.replace(".ca", "")
    
    return canonical
