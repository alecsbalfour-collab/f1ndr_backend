# f1ndr-backend/trinn/utils/normalize_utils.py
"""
DICT-aligned TRINN normalize utilities with enterprise features.
"""

import logging
import re
from typing import Optional, List


logger = logging.getLogger(__name__)


def normalize_title(title: Optional[str]) -> str:
    """
    Normalize title with enterprise text processing.
    
    Args:
        title: Title string to normalize
        
    Returns:
        Normalized title string
    """
    if not title:
        return ""
    
    # Basic whitespace normalization
    normalized = title.strip()
    
    # Remove excessive whitespace
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Remove special characters that might cause issues
    normalized = re.sub(r'[^\w\s\-.,]', '', normalized)
    
    # Trim again after special character removal
    normalized = normalized.strip()
    
    logger.debug(f"Normalized title: '{title}' -> '{normalized}'")
    return normalized


def normalize_price(price: Any) -> Optional[float]:
    """
    Normalize price to float with enterprise validation.
    
    Args:
        price: Price value to normalize
        
    Returns:
        Normalized price as float or None if invalid
    """
    if price is None:
        return None
    
    try:
        # Remove currency symbols and commas
        if isinstance(price, str):
            price = price.replace('$', '').replace(',', '').strip()
        
        normalized_price = float(price)
        
        # Validate price range
        if normalized_price < 0:
            logger.warning(f"Negative price detected: {normalized_price}")
            return None
        
        if normalized_price > 1_000_000_000:  # 1 billion
            logger.warning(f"Suspiciously high price detected: {normalized_price}")
        
        return normalized_price
        
    except (ValueError, TypeError) as e:
        logger.warning(f"Failed to normalize price '{price}': {e}")
        return None


def normalize_location(location: Optional[str]) -> str:
    """
    Normalize location with enterprise geocoding preparation.
    
    Args:
        location: Location string to normalize
        
    Returns:
        Normalized location string
    """
    if not location:
        return ""
    
    # Basic normalization
    normalized = location.strip()
    
    # Standardize common abbreviations
    abbreviations = {
        'st': 'street',
        'ave': 'avenue',
        'blvd': 'boulevard',
        'rd': 'road',
        'dr': 'drive',
        'ln': 'lane',
        'ct': 'court',
        'pl': 'place',
    }
    
    words = normalized.split()
    normalized_words = []
    for word in words:
        lower_word = word.lower()
        if lower_word in abbreviations:
            normalized_words.append(abbreviations[lower_word])
        else:
            normalized_words.append(word)
    
    normalized = ' '.join(normalized_words)
    
    logger.debug(f"Normalized location: '{location}' -> '{normalized}'")
    return normalized


def normalize_field_names(data: Dict[str, Any], field_mappings: Dict[str, str]) -> Dict[str, Any]:
    """
    Normalize field names according to enterprise mapping rules.
    
    Args:
        data: Data dictionary with original field names
        field_mappings: Dictionary mapping original names to canonical names
        
    Returns:
        Data dictionary with normalized field names
    """
    normalized = {}
    
    for original_key, value in data.items():
        # Use mapped name if available, otherwise use original
        normalized_key = field_mappings.get(original_key, original_key)
        normalized[normalized_key] = value
    
    logger.debug(f"Normalized {len(data)} field names")
    return normalized


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
    """
    Validate that required fields are present and non-empty.
    
    Args:
        data: Data dictionary to validate
        required_fields: List of required field names
        
    Returns:
        List of missing field names
    """
    missing_fields = []
    
    for field in required_fields:
        if field not in data or not data[field]:
            missing_fields.append(field)
    
    if missing_fields:
        logger.warning(f"Missing required fields: {missing_fields}")
    
    return missing_fields
