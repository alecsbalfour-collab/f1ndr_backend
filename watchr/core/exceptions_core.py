# f1ndr-backend/watchr/core/exceptions_core.py
"""
Watchr exceptions.
"""

class WatchrError(Exception):
    pass


class ValidationError(WatchrError):
    pass
