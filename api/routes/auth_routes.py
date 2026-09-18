# f1ndr-backend/api/routes/auth_routes.py
"""
DICT-aligned authentication routes with FlutterFlow compatibility and enterprise features.
"""

import logging
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from utils.response_builder import success_response, error_response, unauthorized_response, forbidden_response
from f1ndr.config.auth_config import auth_config


logger = logging.getLogger(__name__)

router = APIRouter(tags=["authentication"])
security = HTTPBearer()


# FlutterFlow-compatible user storage (in production, use MongoDB)
users_db = {}
sessions_db = {}


def create_access_token(user_id: str, additional_claims: Optional[Dict[str, Any]] = None) -> str:
    """
    Create JWT access token with FlutterFlow-compatible claims.
    
    Args:
        user_id: User identifier
        additional_claims: Additional JWT claims
        
    Returns:
        JWT token string
    """
    now = datetime.utcnow()
    expires = now + timedelta(minutes=auth_config.token_expiry_minutes)
    
    claims = {
        "sub": user_id,
        "iat": now.timestamp(),
        "exp": expires.timestamp(),
        "jti": str(uuid.uuid4()),  # JWT ID for token revocation
        "type": "access",
    }
    
    # Add FlutterFlow-specific claims
    if auth_config.flutterflow_app_id:
        claims["app_id"] = auth_config.flutterflow_app_id
    
    # Add additional claims if provided
    if additional_claims:
        claims.update(additional_claims)
    
    token = jwt.encode(claims, auth_config.secret_key, algorithm=auth_config.algorithm)
    logger.info(f"Created access token for user: {user_id}")
    return token


def create_refresh_token(user_id: str) -> str:
    """
    Create JWT refresh token with FlutterFlow compatibility.
    
    Args:
        user_id: User identifier
        
    Returns:
        JWT refresh token string
    """
    now = datetime.utcnow()
    expires = now + timedelta(days=auth_config.refresh_token_expiry_days)
    
    claims = {
        "sub": user_id,
        "iat": now.timestamp(),
        "exp": expires.timestamp(),
        "jti": str(uuid.uuid4()),
        "type": "refresh",
    }
    
    token = jwt.encode(claims, auth_config.secret_key, algorithm=auth_config.algorithm)
    logger.info(f"Created refresh token for user: {user_id}")
    return token


def verify_token(token: str) -> Dict[str, Any]:
    """
    Verify JWT token with enterprise error handling.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token claims
        
    Raises:
        HTTPException: If token is invalid
    """
    try:
        claims = jwt.decode(token, auth_config.secret_key, algorithms=[auth_config.algorithm])
        logger.debug(f"Token verified for user: {claims.get('sub')}")
        return claims
    except JWTError as e:
        logger.warning(f"Token verification failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")


def hash_password(password: str) -> str:
    """
    Hash password with enterprise security.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password
    """
    return hashlib.sha256(password.encode()).hexdigest()


def validate_password_strength(password: str) -> tuple[bool, list]:
    """
    Validate password strength with enterprise requirements.
    
    Args:
        password: Password to validate
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    if len(password) < auth_config.password_min_length:
        errors.append(f"Password must be at least {auth_config.password_min_length} characters")
    
    if auth_config.password_require_uppercase and not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")
    
    if auth_config.password_require_lowercase and not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")
    
    if auth_config.password_require_numbers and not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one number")
    
    if auth_config.password_require_special and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        errors.append("Password must contain at least one special character")
    
    return len(errors) == 0, errors


@router.post("/register")
async def register_user(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Register new user with enterprise validation and FlutterFlow compatibility.
    
    Args:
        user_data: User registration data
        
    Returns:
        FlutterFlow-compatible response with user data and tokens
    """
    try:
        email = user_data.get("email")
        password = user_data.get("password")
        name = user_data.get("name", "")
        
        if not email or not password:
            return error_response(
                message="Email and password are required",
                status_code=400,
                error_code="MISSING_CREDENTIALS"
            )
        
        # Check if user already exists
        if email in users_db:
            return error_response(
                message="User already exists",
                status_code=409,
                error_code="USER_EXISTS"
            )
        
        # Validate password strength
        is_valid, errors = validate_password_strength(password)
        if not is_valid:
            return error_response(
                message="Password does not meet requirements",
                status_code=400,
                details={"password_errors": errors},
                error_code="WEAK_PASSWORD"
            )
        
        # Create user
        user_id = str(uuid.uuid4())
        hashed_password = hash_password(password)
        
        users_db[email] = {
            "user_id": user_id,
            "email": email,
            "password": hashed_password,
            "name": name,
            "created_at": datetime.utcnow().isoformat(),
            "email_verified": False,
        }
        
        # Create tokens
        access_token = create_access_token(user_id, {"email": email, "name": name})
        refresh_token = create_refresh_token(user_id)
        
        logger.info(f"User registered: {email}")
        
        return success_response(
            data={
                "user": {
                    "user_id": user_id,
                    "email": email,
                    "name": name,
                    "email_verified": False,
                },
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "Bearer",
                "expires_in": auth_config.token_expiry_minutes * 60,
            },
            message="User registered successfully",
            status_code=201
        )
        
    except Exception as e:
        logger.error(f"User registration failed: {e}")
        return error_response(
            message=f"Registration failed: {str(e)}",
            status_code=500,
            error_code="REGISTRATION_ERROR"
        )


@router.post("/login")
async def login_user(credentials: Dict[str, Any]) -> Dict[str, Any]:
    """
    Login user with enterprise validation and FlutterFlow compatibility.
    
    Args:
        credentials: Login credentials
        
    Returns:
        FlutterFlow-compatible response with user data and tokens
    """
    try:
        email = credentials.get("email")
        password = credentials.get("password")
        
        if not email or not password:
            return error_response(
                message="Email and password are required",
                status_code=400,
                error_code="MISSING_CREDENTIALS"
            )
        
        # Check if user exists
        if email not in users_db:
            return unauthorized_response(message="Invalid credentials")
        
        user = users_db[email]
        hashed_password = hash_password(password)
        
        # Verify password
        if user["password"] != hashed_password:
            return unauthorized_response(message="Invalid credentials")
        
        # Create tokens
        access_token = create_access_token(user["user_id"], {"email": email, "name": user["name"]})
        refresh_token = create_refresh_token(user["user_id"])
        
        logger.info(f"User logged in: {email}")
        
        return success_response(
            data={
                "user": {
                    "user_id": user["user_id"],
                    "email": user["email"],
                    "name": user["name"],
                    "email_verified": user["email_verified"],
                },
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "Bearer",
                "expires_in": auth_config.token_expiry_minutes * 60,
            },
            message="Login successful"
        )
        
    except Exception as e:
        logger.error(f"Login failed: {e}")
        return error_response(
            message=f"Login failed: {str(e)}",
            status_code=500,
            error_code="LOGIN_ERROR"
        )


@router.post("/refresh")
async def refresh_token(refresh_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Refresh access token with FlutterFlow compatibility.
    
    Args:
        refresh_data: Refresh token data
        
    Returns:
        FlutterFlow-compatible response with new access token
    """
    try:
        refresh_token = refresh_data.get("refresh_token")
        
        if not refresh_token:
            return error_response(
                message="Refresh token is required",
                status_code=400,
                error_code="MISSING_REFRESH_TOKEN"
            )
        
        # Verify refresh token
        claims = verify_token(refresh_token)
        
        if claims.get("type") != "refresh":
            return error_response(
                message="Invalid token type",
                status_code=400,
                error_code="INVALID_TOKEN_TYPE"
            )
        
        user_id = claims.get("sub")
        
        # Create new access token
        access_token = create_access_token(user_id)
        
        logger.info(f"Token refreshed for user: {user_id}")
        
        return success_response(
            data={
                "access_token": access_token,
                "token_type": "Bearer",
                "expires_in": auth_config.token_expiry_minutes * 60,
            },
            message="Token refreshed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        return error_response(
            message=f"Token refresh failed: {str(e)}",
            status_code=500,
            error_code="REFRESH_ERROR"
        )


@router.post("/logout")
async def logout_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Logout user with enterprise session management.
    
    Args:
        credentials: HTTP authorization credentials
        
    Returns:
        FlutterFlow-compatible response
    """
    try:
        token = credentials.credentials
        claims = verify_token(token)
        user_id = claims.get("sub")
        
        # In production, add token to blacklist
        # For now, just log the logout
        logger.info(f"User logged out: {user_id}")
        
        return success_response(
            message="Logout successful"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Logout failed: {e}")
        return error_response(
            message=f"Logout failed: {str(e)}",
            status_code=500,
            error_code="LOGOUT_ERROR"
        )


@router.get("/me")
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Get current user with FlutterFlow compatibility.
    
    Args:
        credentials: HTTP authorization credentials
        
    Returns:
        FlutterFlow-compatible response with user data
    """
    try:
        token = credentials.credentials
        claims = verify_token(token)
        user_id = claims.get("sub")
        
        # Find user by ID
        user = None
        for email, user_data in users_db.items():
            if user_data["user_id"] == user_id:
                user = user_data
                break
        
        if not user:
            return error_response(
                message="User not found",
                status_code=404,
                error_code="USER_NOT_FOUND"
            )
        
        return success_response(
            data={
                "user_id": user["user_id"],
                "email": user["email"],
                "name": user["name"],
                "email_verified": user["email_verified"],
                "created_at": user["created_at"],
            },
            message="User data retrieved"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get current user failed: {e}")
        return error_response(
            message=f"Failed to get user: {str(e)}",
            status_code=500,
            error_code="GET_USER_ERROR"
        )


@router.post("/flutterflow/webhook")
async def flutterflow_webhook(webhook_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    FlutterFlow webhook for authentication events with enterprise handling.
    
    Args:
        webhook_data: FlutterFlow webhook data
        
    Returns:
        FlutterFlow-compatible response
    """
    try:
        # Verify FlutterFlow API key if configured
        if auth_config.flutterflow_api_key:
            api_key = webhook_data.get("api_key")
            if api_key != auth_config.flutterflow_api_key:
                return forbidden_response(message="Invalid API key")
        
        event_type = webhook_data.get("event_type")
        user_data = webhook_data.get("user_data", {})
        
        logger.info(f"FlutterFlow webhook received: {event_type}")
        
        # Handle different FlutterFlow events
        if event_type == "user.created":
            # Handle user creation from FlutterFlow
            email = user_data.get("email")
            if email and email not in users_db:
                user_id = str(uuid.uuid4())
                users_db[email] = {
                    "user_id": user_id,
                    "email": email,
                    "name": user_data.get("name", ""),
                    "created_at": datetime.utcnow().isoformat(),
                    "email_verified": True,  # FlutterFlow verifies email
                }
                logger.info(f"User created via FlutterFlow: {email}")
        
        return success_response(
            message="Webhook processed successfully"
        )
        
    except Exception as e:
        logger.error(f"FlutterFlow webhook failed: {e}")
        return error_response(
            message=f"Webhook processing failed: {str(e)}",
            status_code=500,
            error_code="WEBHOOK_ERROR"
        )