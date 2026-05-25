"""
Auth endpoints — register, login, logout, refresh, me, verify-email, password reset.
"""
import secrets
from datetime import timedelta, datetime, timezone

from fastapi import APIRouter, Cookie, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.core.config import settings
from app.core.database import get_db
from app.core.redis import get_redis
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.schemas.auth import (
    AuthResponse,
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    ResetPasswordRequest,
    UserResponse,
)
from app.services import auth_service, email_service
from app.core.security import create_access_token, create_refresh_token

import redis.asyncio as aioredis

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE = "refresh_token"
COOKIE_MAX_AGE = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=token,
        httponly=True,
        secure=False,           # set True in production (HTTPS only)
        samesite="lax",
        max_age=COOKIE_MAX_AGE,
        path="/api/v1/auth",    # scope cookie to auth routes only
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=REFRESH_COOKIE, path="/api/v1/auth")


# ── Register ───────────────────────────────────────────────────────────────────

@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(
    body: RegisterRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    user, verification_token = await auth_service.register_user(
        db, body.email, body.password, body.full_name
    )

    # Issue tokens immediately so user lands in the app right after signup
    access_token = create_access_token(str(user.id))
    refresh_token_str = create_refresh_token(str(user.id))

    rt = RefreshToken(
        user_id=user.id,
        token_hash=auth_service._hash_token(refresh_token_str),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(rt)

    # Store verification token in Redis (TTL 24h)
    await auth_service.store_verification_token(redis, str(user.id), verification_token)

    # Send verification email — failure is non-fatal
    try:
        email_service.send_verification_email(user.email, verification_token)
    except Exception:
        pass

    _set_refresh_cookie(response, refresh_token_str)
    return AuthResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user),
    )


# ── Login ──────────────────────────────────────────────────────────────────────

@router.post("/login", response_model=AuthResponse)
async def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    ip = request.client.host if request.client else "unknown"
    user, access_token, refresh_token_str = await auth_service.login_user(
        db, redis, body.email, body.password, ip
    )
    _set_refresh_cookie(response, refresh_token_str)
    return AuthResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user),
    )


# ── Refresh ────────────────────────────────────────────────────────────────────

@router.post("/refresh", response_model=dict)
async def refresh(
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE),
    db: AsyncSession = Depends(get_db),
):
    if not refresh_token:
        from app.core.exceptions import UnauthorizedException
        raise UnauthorizedException("No refresh token provided")

    user, new_access_token = await auth_service.refresh_access_token(db, refresh_token)
    return {"access_token": new_access_token, "token_type": "bearer"}


# ── Logout ─────────────────────────────────────────────────────────────────────

@router.post("/logout", response_model=MessageResponse)
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE),
    db: AsyncSession = Depends(get_db),
):
    await auth_service.logout_user(db, refresh_token or "")
    _clear_refresh_cookie(response)
    return MessageResponse(message="Logged out successfully")


# ── Me ─────────────────────────────────────────────────────────────────────────

@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_active_user)):
    return UserResponse.model_validate(current_user)


# ── Verify email ───────────────────────────────────────────────────────────────

@router.get("/verify-email/{token}", response_model=MessageResponse)
async def verify_email(
    token: str,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    await auth_service.verify_email_token(db, redis, token)
    return MessageResponse(message="Email verified successfully")


# ── Forgot password ────────────────────────────────────────────────────────────

@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    body: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    from sqlalchemy import select
    from app.models.user import User as UserModel

    result = await db.execute(select(UserModel).where(UserModel.email == body.email.lower()))
    user = result.scalar_one_or_none()

    # Always return success to prevent email enumeration
    if user and user.is_active:
        reset_token = secrets.token_urlsafe(32)
        await auth_service.store_password_reset_token(redis, str(user.id), reset_token)
        try:
            email_service.send_password_reset_email(user.email, reset_token)
        except Exception:
            pass

    return MessageResponse(message="If that email exists, a reset link has been sent")


# ── Reset password ─────────────────────────────────────────────────────────────

@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    body: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    await auth_service.reset_password(db, redis, body.token, body.password)
    return MessageResponse(message="Password reset successfully")
