"""Authentication request and response models."""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from api.auth.roles import ROLE_SCOPES

Role = Literal[tuple(ROLE_SCOPES)]

# Strength rules live in validate_password_strength; this only bounds the input size.
Password = Field(..., min_length=1, max_length=1024)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Password
    name: str = Field("", max_length=100)


class LoginRequest(BaseModel):
    # Not EmailStr: accounts created before validation must still be able to log in.
    email: str = Field(..., min_length=1, max_length=254)
    password: str = Password


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1, max_length=4096)


class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = Field(None, max_length=4096)


class VerifyEmailRequest(BaseModel):
    token: str = Field(..., min_length=1, max_length=512)


class RolesUpdateRequest(BaseModel):
    roles: List[Role] = Field(..., min_length=1)


class FlutterFlowUser(BaseModel):
    model_config = ConfigDict(extra="allow")
    email: Optional[str] = Field(None, max_length=254)
    name: Optional[str] = Field(None, max_length=100)


class FlutterFlowWebhook(BaseModel):
    model_config = ConfigDict(extra="allow")
    api_key: Optional[str] = Field(None, max_length=512)
    event_type: Optional[str] = Field(None, max_length=100)
    user_data: Optional[FlutterFlowUser] = None


class PublicUser(BaseModel):
    user_id: str
    email: str
    name: str
    email_verified: bool
    roles: List[str]
    created_at: Optional[str] = None


class TokenPair(BaseModel):
    user: PublicUser
    access_token: str
    refresh_token: str
    token_type: Literal["Bearer"]
    expires_in: int


class SessionsRevoked(BaseModel):
    sessions_revoked: int


class AuditEntry(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str
    event: str
    success: bool
    user_id: Optional[str] = None
    actor_id: Optional[str] = None
    email: Optional[str] = None
    details: Dict[str, Any] = {}
    created_at: str
    ip: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
