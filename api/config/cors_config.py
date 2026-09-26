# f1ndr-backend/api/config/cors_config.py
"""
DICT-aligned CORS configuration with FlutterFlow compatibility.
"""

import os
import re
import logging
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from typing import List


logger = logging.getLogger(__name__)


def apply_cors(app: FastAPI) -> None:
    """
    Apply FlutterFlow-compatible CORS configuration to the FastAPI app.
    
    FlutterFlow requires specific CORS settings for proper API integration:
    - Allow credentials for authentication
    - Support FlutterFlow's domain and development environments
    - Allow standard HTTP methods and headers
    """
    
    # FlutterFlow domains (production and development)
    flutterflow_origins = [
        "https://flutterflow.io",
        "https://app.flutterflow.io",
        "https://*.flutterflow.app",  # Custom FlutterFlow apps
        "http://localhost:*",  # Development
        "http://127.0.0.1:*",  # Development
    ]
    
    # Add custom origins from environment if specified
    custom_origins = os.getenv("CORS_ORIGINS", "").split(",")
    if custom_origins and custom_origins[0]:  # Check if not empty
        flutterflow_origins.extend([origin.strip() for origin in custom_origins])
    
    # For development, allow all origins if specified
    if os.getenv("ENVIRONMENT", "development") == "development":
        logger.warning("Development mode: allowing all origins for CORS")
        allow_origins = ["*"]
        allow_origin_regex = None
    else:
        # Starlette matches allow_origins literally, so wildcard entries go into a regex
        allow_origins = [o for o in flutterflow_origins if "*" not in o]
        patterns = [re.escape(o).replace(r"\*", "[A-Za-z0-9-]+") for o in flutterflow_origins if "*" in o]
        allow_origin_regex = "|".join(patterns) or None
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_origin_regex=allow_origin_regex,
        allow_credentials=True,  # Required for FlutterFlow authentication
        allow_methods=[
            "GET",
            "POST",
            "PUT",
            "PATCH",
            "DELETE",
            "OPTIONS",
            "HEAD"
        ],
        allow_headers=[
            "Content-Type",
            "Authorization",
            "X-Requested-With",
            "Accept",
            "Origin",
            "Access-Control-Request-Method",
            "Access-Control-Request-Headers",
            "X-FlutterFlow-App-ID",
            "X-FlutterFlow-User-ID",
        ],
        expose_headers=[
            "Content-Length",
            "Content-Type",
            "X-Total-Count",
            "X-Page-Count",
            "X-Request-ID",
        ],
        max_age=86400,  # 24 hours cache for preflight requests
    )
    
    logger.info(f"CORS configured with {len(allow_origins) if allow_origins != ['*'] else 'unlimited'} origins")
    if allow_origins != ["*"]:
        logger.debug(f"Allowed origins: {allow_origins}")
