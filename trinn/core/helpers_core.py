# f1ndr-backend/trinn/core/helpers_core.py
"""
DICT-aligned TRINN helper utilities with enterprise features.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime


logger = logging.getLogger(__name__)


def safe_get(data: Dict[str, Any], key: str, default: Any = None) -> Any:
    """
    Safely get value from dictionary with enterprise null handling.
    
    Args:
        data: Dictionary to get value from
        key: Key to retrieve
        default: Default value if key not found
        
    Returns:
        Value from dictionary or default
    """
    if data is None:
        logger.warning(f"Attempted to get key '{key}' from None dictionary")
        return default
    
    value = data.get(key, default)
    
    if value is None:
        logger.debug(f"Key '{key}' not found in dictionary, using default")
    
    return value


def safe_get_nested(data: Dict[str, Any], keys: List[str], default: Any = None) -> Any:
    """
    Safely get nested value from dictionary with enterprise path handling.
    
    Args:
        data: Dictionary to get value from
        keys: List of keys representing nested path
        default: Default value if path not found
        
    Returns:
        Value from nested path or default
    """
    if data is None:
        logger.warning(f"Attempted to get nested path {keys} from None dictionary")
        return default
    
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            logger.debug(f"Nested path {keys} not found, using default")
            return default
    
    return current


def format_timestamp(timestamp: Optional[str], format_string: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format timestamp with enterprise error handling.
    
    Args:
        timestamp: ISO format timestamp string
        format_string: Desired output format
        
    Returns:
        Formatted timestamp string
    """
    if not timestamp:
        return "N/A"
    
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.strftime(format_string)
    except Exception as e:
        logger.warning(f"Failed to format timestamp '{timestamp}': {e}")
        return timestamp


def truncate_string(text: Optional[str], max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate string to maximum length with enterprise safety.
    
    Args:
        text: String to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated string
    """
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def safe_int(value: Any, default: int = 0) -> int:
    """
    Safely convert value to integer with enterprise error handling.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        Integer value or default
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        logger.warning(f"Failed to convert '{value}' to int, using default {default}")
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """
    Safely convert value to float with enterprise error handling.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        Float value or default
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        logger.warning(f"Failed to convert '{value}' to float, using default {default}")
        return default


def safe_bool(value: Any, default: bool = False) -> bool:
    """
    Safely convert value to boolean with enterprise error handling.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        Boolean value or default
    """
    if isinstance(value, bool):
        return value
    
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes', 'on')
    
    try:
        return bool(value)
    except Exception:
        logger.warning(f"Failed to convert '{value}' to bool, using default {default}")
        return default


def chunk_list(items: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split list into chunks with enterprise batch processing support.
    
    Args:
        items: List to chunk
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
    """
    chunks = []
    for i in range(0, len(items), chunk_size):
        chunks.append(items[i:i + chunk_size])
    
    logger.debug(f"Chunked list of {len(items)} items into {len(chunks)} chunks of size {chunk_size}")
    return chunks


def retry_with_backoff(func, max_retries: int = 3, base_delay: float = 1.0):
    """
    Execute function with exponential backoff retry logic.
    
    Args:
        func: Function to execute
        max_retries: Maximum number of retry attempts
        base_delay: Base delay between retries in seconds
        
    Returns:
        Function result
    """
    import time
    import random
    
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            
            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
            logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay:.2f}s: {e}")
            time.sleep(delay)
