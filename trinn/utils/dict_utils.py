# f1ndr-backend/trinn/utils/dict_utils.py
"""
DICT-aligned TRINN dictionary utilities with enterprise features.
"""

import logging
from typing import Dict, Any, List, Optional, Set
from copy import deepcopy


logger = logging.getLogger(__name__)


def merge_dicts(base: Dict[str, Any], updates: Dict[str, Any], deep: bool = False) -> Dict[str, Any]:
    """
    Merge dictionaries with enterprise options for deep merging.
    
    Args:
        base: Base dictionary
        updates: Dictionary with updates to apply
        deep: Whether to perform deep merge
        
    Returns:
        Merged dictionary
    """
    if deep:
        return _deep_merge_dicts(base, updates)
    else:
        merged = base.copy()
        merged.update(updates)
        logger.debug(f"Merged dictionaries (shallow): {len(base)} + {len(updates)} keys")
        return merged


def _deep_merge_dicts(base: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge dictionaries with enterprise conflict resolution.
    
    Args:
        base: Base dictionary
        updates: Dictionary with updates to apply
        
    Returns:
        Deep merged dictionary
    """
    result = deepcopy(base)
    
    for key, value in updates.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge_dicts(result[key], value)
        else:
            result[key] = deepcopy(value)
    
    logger.debug(f"Deep merged dictionaries: {len(base)} + {len(updates)} keys")
    return result


def filter_keys(data: Dict[str, Any], allowed: List[str], case_sensitive: bool = True) -> Dict[str, Any]:
    """
    Filter dictionary to only include allowed keys with enterprise options.
    
    Args:
        data: Dictionary to filter
        allowed: List of allowed key names
        case_sensitive: Whether key matching should be case sensitive
        
    Returns:
        Filtered dictionary
    """
    if not case_sensitive:
        allowed_lower = {key.lower(): key for key in allowed}
        filtered = {}
        for k, v in data.items():
            if k.lower() in allowed_lower:
                filtered[allowed_lower[k.lower()]] = v
    else:
        allowed_set = set(allowed)
        filtered = {k: v for k, v in data.items() if k in allowed_set}
    
    logger.debug(f"Filtered dictionary: {len(data)} -> {len(filtered)} keys")
    return filtered


def remove_keys(data: Dict[str, Any], keys_to_remove: List[str]) -> Dict[str, Any]:
    """
    Remove specified keys from dictionary with enterprise safety.
    
    Args:
        data: Dictionary to process
        keys_to_remove: List of key names to remove
        
    Returns:
        Dictionary with specified keys removed
    """
    result = data.copy()
    remove_set = set(keys_to_remove)
    
    for key in remove_set:
        if key in result:
            del result[key]
    
    logger.debug(f"Removed {len(remove_set & set(result.keys()))} keys from dictionary")
    return result


def rename_keys(data: Dict[str, Any], key_mappings: Dict[str, str]) -> Dict[str, Any]:
    """
    Rename dictionary keys according to enterprise mapping rules.
    
    Args:
        data: Dictionary with original key names
        key_mappings: Dictionary mapping old names to new names
        
    Returns:
        Dictionary with renamed keys
    """
    result = {}
    
    for old_key, value in data.items():
        new_key = key_mappings.get(old_key, old_key)
        result[new_key] = value
    
    logger.debug(f"Renamed {len([k for k in key_mappings if k in data])} keys")
    return result


def flatten_dict(data: Dict[str, Any], separator: str = ".", prefix: str = "") -> Dict[str, Any]:
    """
    Flatten nested dictionary with enterprise configuration.
    
    Args:
        data: Dictionary to flatten
        separator: Separator for nested keys
        prefix: Prefix for flattened keys
        
    Returns:
        Flattened dictionary
    """
    result = {}
    
    for key, value in data.items():
        new_key = f"{prefix}{separator}{key}" if prefix else key
        
        if isinstance(value, dict):
            result.update(flatten_dict(value, separator, new_key))
        else:
            result[new_key] = value
    
    logger.debug(f"Flattened dictionary: {len(data)} -> {len(result)} keys")
    return result


def sanitize_dict(data: Dict[str, Any], sensitive_keys: Optional[Set[str]] = None) -> Dict[str, Any]:
    """
    Sanitize dictionary by removing or masking sensitive data.
    
    Args:
        data: Dictionary to sanitize
        sensitive_keys: Set of sensitive key names to mask
        
    Returns:
        Sanitized dictionary
    """
    if sensitive_keys is None:
        sensitive_keys = {"password", "token", "secret", "api_key", "credit_card"}
    
    result = data.copy()
    
    for key in sensitive_keys:
        if key in result:
            result[key] = "***REDACTED***"
    
    logger.debug(f"Sanitized dictionary: masked {len(sensitive_keys & set(result.keys()))} sensitive keys")
    return result


def validate_dict_structure(data: Dict[str, Any], required_keys: List[str]) -> bool:
    """
    Validate dictionary structure with enterprise rules.
    
    Args:
        data: Dictionary to validate
        required_keys: List of required key names
        
    Returns:
        True if dictionary is valid
    """
    missing_keys = [key for key in required_keys if key not in data]
    
    if missing_keys:
        logger.warning(f"Dictionary validation failed: missing keys {missing_keys}")
        return False
    
    logger.debug("Dictionary structure validation passed")
    return True
