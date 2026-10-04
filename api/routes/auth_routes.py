# f1ndr-backend/api/routes/auth_routes.py
"""
Authentication routes: registration, login with lockout, rotating refresh tokens,
logout/revocation, email verification, role management, and the audit trail.
"""

import logging
import secrets
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request

from api.auth import accounts
from api.auth.audit import list_audit, record_audit
from api.auth.email import send_email
from api.auth.passwords import hash_password, validate_password_strength, verify_password
from api.auth.tokens import (
    RefreshTokenReused,
    access_claims_for,
    create_access_token,
    create_refresh_token,
    issue_refresh_token,
    revoke_access_token,
    revoke_all_refresh_tokens,
    revoke_refresh_token,
    rotate_refresh_token,
    verify_token,
)
from api.config.settings_config import get_settings
from api.dependencies.auth import require_scopes, require_user
from api.schemas.auth_schemas import (
    AuditEntry,
    FlutterFlowWebhook,
    LoginRequest,
    LogoutRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    PublicUser,
    RefreshRequest,
    RegisterRequest,
    RolesUpdateRequest,
    SessionsRevoked,
    TokenPair,
    VerifyEmailRequest,
)
from api.schemas.common import Envelope, error_responses, ok
from api.security.rate_limiter import LOGIN_RATE_LIMIT, PASSWORD_RESET_RATE_LIMIT, REGISTER_RATE_LIMIT, limiter
from f1ndr.config.auth_config import auth_config
from utils.response_builder import error_response, forbidden_response, not_found_response, unauthorized_response

__all__ = ["router", "create_access_token", "create_refresh_token", "verify_token", "hash_password"]

logger = logging.getLogger(__name__)

router = APIRouter(tags=["authentication"])


async def _token_payload(user: dict, refresh_token: str) -> Dict[str, Any]:
    return {
        "user": accounts.public_user(user),
        "access_token": create_access_token(user["user_id"], access_claims_for(user)),
        "refresh_token": refresh_token,
        "token_type": "Bearer",
        "expires_in": auth_config.token_expiry_minutes * 60,
    }


async def _send_verification_email(request: Request, background_tasks: BackgroundTasks, user: dict) -> None:
    token = await accounts.create_email_verification_token(user)
    base = get_settings().EMAIL_VERIFICATION_URL or str(request.url_for("verify_email_link"))
    link = f"{base}{'&' if '?' in base else '?'}token={token}"
    body = (
        f"Hi {user.get('name') or 'there'},\n\n"
        f"Confirm your email address for f1ndr by opening this link:\n\n{link}\n\n"
        f"The link expires in {auth_config.email_verification_expiry_hours} hours. "
        "If you didn't create an account, you can ignore this email.\n"
    )
    background_tasks.add_task(send_email, user["email"], "Verify your f1ndr email address", body)
    await record_audit("email_verification_sent", request, user_id=user["user_id"], email=user["email"])


@router.post("/register", status_code=201, response_model=Envelope[TokenPair], responses=error_responses(400, 409))
@limiter.limit(REGISTER_RATE_LIMIT)
async def register_user(request: Request, background_tasks: BackgroundTasks, body: RegisterRequest):
    email, password = accounts.normalize_email(body.email), body.password
    is_valid, errors = validate_password_strength(password)
    if not is_valid:
        return error_response(
            message="Password does not meet requirements",
            status_code=400,
            details={"password_errors": errors},
            error_code="WEAK_PASSWORD",
        )

    try:
        user = await accounts.create_user(email, hash_password(password), name=body.name)
    except accounts.UserExistsError:
        return error_response(message="User already exists", status_code=409, error_code="USER_EXISTS")

    await record_audit("register", request, user_id=user["user_id"], email=email)
    await _send_verification_email(request, background_tasks, user)
    data = await _token_payload(user, await issue_refresh_token(user["user_id"]))
    return ok(data, "User registered successfully")


@router.post("/login", response_model=Envelope[TokenPair], responses=error_responses(401, 423))
@limiter.limit(LOGIN_RATE_LIMIT)
async def login_user(request: Request, body: LoginRequest):
    email, password = accounts.normalize_email(body.email), body.password
    user = await accounts.get_user_by_email(email)
    if user is None:
        verify_password(password, None)
        await record_audit("login_failed", request, email=email, success=False, details={"reason": "unknown_email"})
        return unauthorized_response(message="Invalid credentials")

    locked_for = accounts.lock_remaining_seconds(user)
    if locked_for:
        await record_audit("login_blocked", request, user_id=user["user_id"], email=email, success=False)
        response = error_response(
            message="Account temporarily locked. Try again later.", status_code=423, error_code="ACCOUNT_LOCKED"
        )
        response.headers["Retry-After"] = str(locked_for)
        return response

    if not verify_password(password, user.get("password_hash")):
        await record_audit("login_failed", request, user_id=user["user_id"], email=email, success=False,
                           details={"reason": "bad_password"})
        if await accounts.register_failed_login(user):
            await record_audit("account_locked", request, user_id=user["user_id"], email=email,
                               details={"minutes": auth_config.lockout_duration_minutes})
        return unauthorized_response(message="Invalid credentials")

    await accounts.record_login(user["user_id"])
    await record_audit("login", request, user_id=user["user_id"], email=email)
    data = await _token_payload(user, await issue_refresh_token(user["user_id"]))
    return ok(data, "Login successful")


@router.post("/refresh", response_model=Envelope[TokenPair], responses=error_responses(401))
async def refresh_token(request: Request, body: RefreshRequest):
    try:
        claims = await rotate_refresh_token(body.refresh_token)
    except RefreshTokenReused as exc:
        await record_audit("refresh_token_reuse", request, user_id=exc.user_id, success=False,
                           details={"family": exc.family})
        raise

    user = await accounts.get_user(claims["sub"])
    if user is None:
        await revoke_all_refresh_tokens(claims["sub"], "user_missing")
        return unauthorized_response(message="Invalid token")

    await record_audit("token_refresh", request, user_id=user["user_id"])
    data = await _token_payload(user, claims["new_refresh_token"])
    return ok(data, "Token refreshed successfully")


@router.post("/logout", response_model=Envelope[None], responses=error_responses(401))
async def logout_user(
    request: Request,
    claims: Dict[str, Any] = Depends(require_user),
    body: Optional[LogoutRequest] = None,
):
    """Revoke this access token and, if provided, the session of `refresh_token`."""
    await revoke_access_token(claims)
    refresh = body.refresh_token if body else None
    session_revoked = bool(refresh) and await revoke_refresh_token(refresh, claims["sub"])
    await record_audit("logout", request, user_id=claims["sub"], details={"session_revoked": bool(session_revoked)})
    return ok(message="Logout successful")


@router.post("/logout-all", response_model=Envelope[SessionsRevoked], responses=error_responses(401))
async def logout_all(request: Request, claims: Dict[str, Any] = Depends(require_user)):
    """Revoke every refresh token for the user. Other access tokens expire within `expires_in`."""
    await revoke_access_token(claims)
    revoked = await revoke_all_refresh_tokens(claims["sub"], "logout_all")
    await record_audit("logout_all", request, user_id=claims["sub"], details={"sessions_revoked": revoked})
    return ok({"sessions_revoked": revoked}, "All sessions logged out")


@router.get("/me", response_model=Envelope[PublicUser], responses=error_responses(401, 404))
async def get_current_user(claims: Dict[str, Any] = Depends(require_user)):
    user = await accounts.get_user(claims["sub"])
    if not user:
        return error_response(message="User not found", status_code=404, error_code="USER_NOT_FOUND")
    return ok(accounts.public_user(user), "User data retrieved")


@router.get("/me/audit", response_model=Envelope[List[AuditEntry]], responses=error_responses(401))
async def get_my_audit(
    claims: Dict[str, Any] = Depends(require_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    entries = await list_audit({"user_id": claims["sub"]}, skip=skip, limit=limit)
    return ok(entries, "Audit events retrieved")


async def _verify_email(request: Request, token: str):
    user = await accounts.verify_email_token(token)
    if user is None:
        return error_response(message="Invalid or expired verification token", status_code=400,
                              error_code="INVALID_VERIFICATION_TOKEN")
    await record_audit("email_verified", request, user_id=user["user_id"], email=user["email"])
    return ok(accounts.public_user(user), "Email verified")


@router.post("/verify-email", response_model=Envelope[PublicUser], responses=error_responses(400))
async def verify_email(request: Request, body: VerifyEmailRequest):
    return await _verify_email(request, body.token)


@router.get("/verify-email", name="verify_email_link", response_model=Envelope[PublicUser],
            responses=error_responses(400))
async def verify_email_link(request: Request, token: str = Query(..., min_length=1, max_length=512)):
    return await _verify_email(request, token)


@router.post("/password-reset/request", response_model=Envelope[None])
@limiter.limit(PASSWORD_RESET_RATE_LIMIT)
async def request_password_reset(request: Request, background_tasks: BackgroundTasks, body: PasswordResetRequest):
    """
    Email a single-use reset link. Always returns the same 200 so callers
    can't probe whether an email has an account.
    """
    user = await accounts.get_user_by_email(body.email)
    if user is not None:
        token = await accounts.create_password_reset_token(user)
        # The link must land on the app's reset form, which POSTs token + new password to /confirm.
        base = get_settings().PASSWORD_RESET_URL or str(request.url_for("confirm_password_reset"))
        link = f"{base}{'&' if '?' in base else '?'}token={token}"
        email_body = (
            f"Hi {user.get('name') or 'there'},\n\n"
            f"Reset your f1ndr password by opening this link:\n\n{link}\n\n"
            f"The link expires in {auth_config.password_reset_expiry_minutes} minutes and works once. "
            "If you didn't ask for this, you can ignore this email.\n"
        )
        background_tasks.add_task(send_email, user["email"], "Reset your f1ndr password", email_body)
        await record_audit("password_reset_requested", request, user_id=user["user_id"], email=user["email"])
    else:
        await record_audit("password_reset_requested", request, email=body.email, success=False,
                           details={"reason": "unknown_email"})
    return ok(message="If that email has an account, a reset link is on its way")


@router.post("/password-reset/confirm", name="confirm_password_reset",
             response_model=Envelope[SessionsRevoked], responses=error_responses(400))
@limiter.limit(LOGIN_RATE_LIMIT)
async def confirm_password_reset(request: Request, body: PasswordResetConfirm):
    """
    Consume a reset token and set the new password. Revokes every refresh-token
    session; outstanding access tokens expire with their normal `expires_in`.
    """
    is_valid, errors = validate_password_strength(body.password)
    if not is_valid:
        return error_response(
            message="Password does not meet requirements",
            status_code=400,
            details={"password_errors": errors},
            error_code="WEAK_PASSWORD",
        )

    user = await accounts.consume_password_reset_token(body.token)
    if user is None:
        await record_audit("password_reset_failed", request, success=False, details={"reason": "invalid_token"})
        return error_response(message="Invalid or expired reset token", status_code=400,
                              error_code="INVALID_RESET_TOKEN")

    await accounts.set_password(user["user_id"], hash_password(body.password))
    revoked = await revoke_all_refresh_tokens(user["user_id"], "password_reset")
    await record_audit("password_reset", request, user_id=user["user_id"], email=user["email"],
                       details={"sessions_revoked": revoked})
    return ok({"sessions_revoked": revoked}, "Password updated; all sessions signed out")


@router.post("/verify-email/resend", response_model=Envelope[None], responses=error_responses(400, 401, 404))
async def resend_verification_email(
    request: Request, background_tasks: BackgroundTasks, claims: Dict[str, Any] = Depends(require_user)
):
    user = await accounts.get_user(claims["sub"])
    if user is None:
        return error_response(message="User not found", status_code=404, error_code="USER_NOT_FOUND")
    if user.get("email_verified"):
        return error_response(message="Email already verified", status_code=400, error_code="ALREADY_VERIFIED")
    await _send_verification_email(request, background_tasks, user)
    return ok(message="Verification email sent")


@router.get("/audit", response_model=Envelope[List[AuditEntry]], responses=error_responses(401, 403))
async def get_audit_log(
    claims: Dict[str, Any] = Depends(require_scopes("audit:read")),
    user_id: Optional[str] = None,
    event: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    query = {k: v for k, v in {"user_id": user_id, "event": event}.items() if v is not None}
    return ok(await list_audit(query, skip=skip, limit=limit), "Audit events retrieved")


@router.put("/users/{user_id}/roles", response_model=Envelope[PublicUser], responses=error_responses(401, 403, 404))
async def update_user_roles(
    user_id: str,
    request: Request,
    body: RolesUpdateRequest,
    claims: Dict[str, Any] = Depends(require_scopes("users:admin")),
):
    previous = await accounts.get_user(user_id)
    if previous is None:
        return not_found_response("User", user_id)
    user = await accounts.set_roles(user_id, body.roles)
    await record_audit("roles_changed", request, user_id=user_id, actor_id=claims["sub"],
                       details={"from": previous.get("roles", []), "to": user["roles"]})
    return ok(accounts.public_user(user), "Roles updated; applies on next token refresh")


@router.post("/users/{user_id}/unlock", response_model=Envelope[None], responses=error_responses(401, 403, 404))
async def unlock_user(user_id: str, request: Request, claims: Dict[str, Any] = Depends(require_scopes("users:admin"))):
    if not await accounts.clear_lockout(user_id):
        return not_found_response("User", user_id)
    await record_audit("account_unlocked", request, user_id=user_id, actor_id=claims["sub"])
    return ok(message="Account unlocked")


@router.post("/flutterflow/webhook", response_model=Envelope[None], responses=error_responses(403))
async def flutterflow_webhook(request: Request, body: FlutterFlowWebhook):
    expected_key = auth_config.flutterflow_api_key
    if expected_key:
        if not body.api_key or not secrets.compare_digest(body.api_key, expected_key):
            return forbidden_response(message="Invalid API key")
    elif get_settings().ENVIRONMENT == "production":
        logger.error("FLUTTERFLOW_API_KEY not configured; rejecting webhook")
        return forbidden_response(message="Webhook not configured")

    logger.info("FlutterFlow webhook received: %s", body.event_type)

    user_data = body.user_data
    email = user_data.email if user_data else None
    if body.event_type == "user.created" and email and email.strip():
        try:
            # FlutterFlow verified the email; the account has no password here, so it can't log in via /login
            user = await accounts.create_user(email, None, name=user_data.name or "", email_verified=True)
        except accounts.UserExistsError:
            pass
        else:
            await record_audit("register", request, user_id=user["user_id"], email=user["email"],
                               details={"source": "flutterflow"})

    return ok(message="Webhook processed successfully")
