# f1ndr-backend/f1ndr/config/auth_config.py
"""
DICT-aligned authentication configuration with FlutterFlow compatibility and enterprise features.
"""

import os
import logging
from dataclasses import dataclass
from typing import List, Optional


logger = logging.getLogger(__name__)


@dataclass
class AuthConfig:
    """Enterprise authentication configuration with DICT patterns and FlutterFlow compatibility."""
    feature_key: str = "auth"
    feature_version: str = "1.0.0"
    enabled: bool = True
    
    # JWT Configuration
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    token_expiry_minutes: int = 60
    refresh_token_expiry_days: int = 7
    
    # FlutterFlow-specific settings
    flutterflow_app_id: Optional[str] = None
    flutterflow_api_key: Optional[str] = None
    support_flutterflow_auth: bool = True
    
    # User management
    require_email_verification: bool = True
    password_min_length: int = 8
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_numbers: bool = True
    password_require_special: bool = True
    
    # Session management
    max_sessions_per_user: int = 5
    session_timeout_minutes: int = 30
    
    # Rate limiting
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15
    
    # OAuth providers (FlutterFlow compatible)
    oauth_providers: List[str] = None
    
    def __post_init__(self):
        if self.oauth_providers is None:
            self.oauth_providers = ["google", "apple", "facebook"]
        
        # Override with environment variables if available
        self.secret_key = os.getenv("JWT_SECRET", self.secret_key)
        self.token_expiry_minutes = int(os.getenv("TOKEN_EXPIRY_MINUTES", str(self.token_expiry_minutes)))
        self.flutterflow_app_id = os.getenv("FLUTTERFLOW_APP_ID", self.flutterflow_app_id)
        self.flutterflow_api_key = os.getenv("FLUTTERFLOW_API_KEY", self.flutterflow_api_key)


auth_config = AuthConfig()
