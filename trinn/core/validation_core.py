# f1ndr-backend/trinn/core/validation_core.py
"""
DICT-aligned TRINN validation utilities with enterprise features.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime


logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Enterprise validation result with DICT patterns."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    validated_fields: List[str]
    timestamp: str
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()


def require_fields(data: Dict[str, Any], fields: List[str]) -> bool:
    """
    Validate that required fields are present with enterprise error tracking.
    
    Args:
        data: Data dictionary to validate
        fields: List of required field names
        
    Returns:
        True if all required fields are present
    """
    missing = [f for f in fields if f not in data]
    
    if missing:
        logger.warning(f"Missing required fields: {missing}")
        return False
    
    logger.debug(f"All required fields present: {fields}")
    return True


def validate_field_types(data: Dict[str, Any], field_types: Dict[str, type]) -> ValidationResult:
    """
    Validate field types with enterprise type checking.
    
    Args:
        data: Data dictionary to validate
        field_types: Dictionary mapping field names to expected types
        
    Returns:
        ValidationResult with validation details
    """
    errors = []
    warnings = []
    validated_fields = []
    
    for field, expected_type in field_types.items():
        if field in data:
            value = data[field]
            if not isinstance(value, expected_type):
                errors.append(f"Field '{field}' has wrong type: expected {expected_type}, got {type(value)}")
            else:
                validated_fields.append(field)
        else:
            warnings.append(f"Field '{field}' not found in data")
    
    is_valid = len(errors) == 0
    result = ValidationResult(
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
        validated_fields=validated_fields,
        timestamp=datetime.utcnow().isoformat(),
    )
    
    logger.info(f"Field type validation: {len(validated_fields)} valid, {len(errors)} errors")
    return result


def validate_field_ranges(data: Dict[str, Any], field_ranges: Dict[str, tuple]) -> ValidationResult:
    """
    Validate field value ranges with enterprise range checking.
    
    Args:
        data: Data dictionary to validate
        field_ranges: Dictionary mapping field names to (min, max) tuples
        
    Returns:
        ValidationResult with validation details
    """
    errors = []
    warnings = []
    validated_fields = []
    
    for field, (min_val, max_val) in field_ranges.items():
        if field in data:
            value = data[field]
            try:
                numeric_value = float(value)
                if numeric_value < min_val or numeric_value > max_val:
                    errors.append(f"Field '{field}' value {numeric_value} out of range [{min_val}, {max_val}]")
                else:
                    validated_fields.append(field)
            except (ValueError, TypeError):
                errors.append(f"Field '{field}' value '{value}' cannot be converted to numeric")
        else:
            warnings.append(f"Field '{field}' not found in data")
    
    is_valid = len(errors) == 0
    result = ValidationResult(
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
        validated_fields=validated_fields,
        timestamp=datetime.utcnow().isoformat(),
    )
    
    logger.info(f"Field range validation: {len(validated_fields)} valid, {len(errors)} errors")
    return result


def validate_string_lengths(data: Dict[str, Any], field_lengths: Dict[str, tuple]) -> ValidationResult:
    """
    Validate string field lengths with enterprise length checking.
    
    Args:
        data: Data dictionary to validate
        field_lengths: Dictionary mapping field names to (min_length, max_length) tuples
        
    Returns:
        ValidationResult with validation details
    """
    errors = []
    warnings = []
    validated_fields = []
    
    for field, (min_len, max_len) in field_lengths.items():
        if field in data:
            value = data[field]
            if isinstance(value, str):
                length = len(value)
                if length < min_len or length > max_len:
                    errors.append(f"Field '{field}' length {length} out of range [{min_len}, {max_len}]")
                else:
                    validated_fields.append(field)
            else:
                errors.append(f"Field '{field}' is not a string")
        else:
            warnings.append(f"Field '{field}' not found in data")
    
    is_valid = len(errors) == 0
    result = ValidationResult(
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
        validated_fields=validated_fields,
        timestamp=datetime.utcnow().isoformat(),
    )
    
    logger.info(f"String length validation: {len(validated_fields)} valid, {len(errors)} errors")
    return result


def validate_data_integrity(data: Dict[str, Any], checksum: Optional[str] = None) -> ValidationResult:
    """
    Validate data integrity with enterprise checksum verification.
    
    Args:
        data: Data dictionary to validate
        checksum: Optional expected checksum
        
    Returns:
        ValidationResult with validation details
    """
    errors = []
    warnings = []
    validated_fields = list(data.keys())
    
    # Basic integrity checks
    if not data:
        errors.append("Data dictionary is empty")
    
    # Check for None values in critical fields
    critical_fields = ["id", "title"]  # Example critical fields
    for field in critical_fields:
        if field in data and data[field] is None:
            errors.append(f"Critical field '{field}' has None value")
    
    # Checksum validation if provided
    if checksum:
        calculated_checksum = _calculate_checksum(data)
        if calculated_checksum != checksum:
            errors.append(f"Checksum mismatch: expected {checksum}, got {calculated_checksum}")
        else:
            validated_fields.append("checksum")
    
    is_valid = len(errors) == 0
    result = ValidationResult(
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
        validated_fields=validated_fields,
        timestamp=datetime.utcnow().isoformat(),
    )
    
    logger.info(f"Data integrity validation: {len(validated_fields)} valid, {len(errors)} errors")
    return result


def _calculate_checksum(data: Dict[str, Any]) -> str:
    """Calculate simple checksum for data integrity validation."""
    import hashlib
    data_str = str(sorted(data.items()))
    return hashlib.md5(data_str.encode()).hexdigest()


async def async_validate_data(data: Dict[str, Any], validators: List[callable]) -> ValidationResult:
    """
    Run multiple validators asynchronously with enterprise orchestration.
    
    Args:
        data: Data dictionary to validate
        validators: List of validation functions to run
        
    Returns:
        Combined ValidationResult from all validators
    """
    all_errors = []
    all_warnings = []
    all_validated_fields = []
    
    for validator in validators:
        try:
            result = validator(data)
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)
            all_validated_fields.extend(result.validated_fields)
        except Exception as e:
            logger.error(f"Validator failed: {e}")
            all_errors.append(f"Validator error: {str(e)}")
    
    # Remove duplicates
    all_validated_fields = list(set(all_validated_fields))
    
    is_valid = len(all_errors) == 0
    result = ValidationResult(
        is_valid=is_valid,
        errors=all_errors,
        warnings=all_warnings,
        validated_fields=all_validated_fields,
        timestamp=datetime.utcnow().isoformat(),
    )
    
    logger.info(f"Async validation complete: {len(all_validated_fields)} fields validated")
    return result
