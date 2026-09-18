# f1ndr-backend/watchr/utils/dict_utils.py
"""
Dictionary utilities.
"""

def merge_dicts(base: dict, updates: dict) -> dict:
    merged = base.copy()
    merged.update(updates)
    return merged
