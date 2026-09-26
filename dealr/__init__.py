"""
dealr feature package for f1ndr.
"""

from .config.dealr_config import dealr_config, get_dealr_config
from .module import run

__all__ = ["dealr_config", "get_dealr_config", "run"]
