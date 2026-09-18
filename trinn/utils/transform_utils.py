# f1ndr-backend/trinn/utils/transform_utils.py
"""
DICT-aligned TRINN transform utilities with enterprise features.
"""

import logging
import re
from typing import Dict, Any, Optional, Callable


logger = logging.getLogger(__name__)


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
    canonical = canonical.replace(".org", "")
    canonical = canonical.replace(".net", "")
    
    # Remove special characters
    canonical = re.sub(r'[^\w\-]', '_', canonical)
    
    # Remove consecutive underscores
    canonical = re.sub(r'_+', '_', canonical)
    
    # Strip trailing/leading underscores
    canonical = canonical.strip('_')
    
    logger.debug(f"Mapped source '{source}' to canonical '{canonical}'")
    return canonical


def apply_field_transformations(data: Dict[str, Any], transformations: Dict[str, Callable]) -> Dict[str, Any]:
    """
    Apply field transformations with enterprise error handling.
    
    Args:
        data: Data to transform
        transformations: Dictionary mapping field names to transformation functions
        
    Returns:
        Transformed data dictionary
    """
    result = data.copy()
    
    for field, transform_func in transformations.items():
        if field in result:
            try:
                original_value = result[field]
                transformed_value = transform_func(original_value)
                result[field] = transformed_value
                logger.debug(f"Transformed field '{field}': {original_value} -> {transformed_value}")
            except Exception as e:
                logger.warning(f"Failed to transform field '{field}': {e}")
                # Keep original value on transformation failure
    
    return result


def validate_canonical_source(source: str) -> bool:
    """
    Validate canonical source format.
    
    Args:
        source: Source string to validate
        
    Returns:
        True if source is valid
    """
    if not source or source == "unknown":
        return False
    
    # Check for minimum length
    if len(source) < 2:
        return False
    
    # Check for valid characters
    if not re.match(r'^[a-z0-9_\-]+$', source):
        return False
    
    return True
