# f1ndr-backend/watchr/utils/diff_utils.py
"""
Diff utilities.
"""

def diff(a: dict, b: dict) -> dict:
    return {k: (a.get(k), b.get(k)) for k in set(a) | set(b) if a.get(k) != b.get(k)}
