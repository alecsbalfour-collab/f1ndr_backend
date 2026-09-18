# f1ndr-backend/trinn/data/enrich_data.py
"""
DICT-aligned TRINN enrich data builders with enterprise features.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class EnrichPayload:
    """Enterprise enrich payload with DICT patterns."""
    source: Optional[str] = None
    raw: Dict[str, Any] = None
    metadata: Dict[str, Any] = None
    enriched_at: str = None
    processing_version: str = "1.0.0"
    
    def __post_init__(self):
        if self.raw is None:
            self.raw = {}
        if self.metadata is None:
            self.metadata = {}
        if self.enriched_at is None:
            self.enriched_at = datetime.utcnow().isoformat()


def build_enrich_payload(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build enrich payload with enterprise metadata.
    
    Args:
        raw: Raw data to enrich
        
    Returns:
        Dictionary with enriched data and metadata
    """
    try:
        payload = EnrichPayload(
            source=raw.get("source"),
            raw=raw,
            metadata=raw.get("metadata", {}),
        )
        
        result = {
            "source": payload.source,
            "raw": payload.raw,
            "metadata": payload.metadata,
            "enriched_at": payload.enriched_at,
            "processing_version": payload.processing_version,
        }
        
        logger.debug(f"Built enrich payload for source: {payload.source}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to build enrich payload: {e}")
        raise


def build_enrich_metadata(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build enrichment metadata with enterprise tracking.
    
    Args:
        raw: Raw data to extract metadata from
        
    Returns:
        Dictionary with enrichment metadata
    """
    metadata = {
        "timestamp": datetime.utcnow().isoformat(),
        "processing_stage": "enrich",
        "data_size_bytes": len(str(raw)),
        "field_count": len(raw.keys()),
    }
    
    # Add source-specific metadata
    source = raw.get("source")
    if source:
        metadata["source"] = source
        metadata["source_type"] = _determine_source_type(source)
    
    return metadata


def _determine_source_type(source: str) -> str:
    """Determine the type of data source."""
    if not source:
        return "unknown"
    
    source_lower = source.lower()
    
    if any(platform in source_lower for platform in ["kijiji", "facebook", "autotrader"]):
        return "marketplace"
    elif any(platform in source_lower for platform in ["realtor", "zillow"]):
        return "real_estate"
    elif "dealr" in source_lower:
        return "dealer"
    else:
        return "general"
