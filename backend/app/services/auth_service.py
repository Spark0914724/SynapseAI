"""
Auth service — all business logic for authentication.
Keeps the endpoint layer thin.
"""
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import redis.asyncio as aioredis

from app.core.config import settings
from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    UnauthorizedException,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.refresh_token import RefreshToken
from app.models.subscription import PlanType, Subscription, SubscriptionStatus
from app.models.user import User
from app.schemas.auth import AuthResponse, UserResponse


# ── Helpers ────────────────────────────────────────────────────────────────────

def _hash_token(token: str) -> str:
    """SHA-256 hash a token for safe DB storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def _user_to_response(user: User) -> UserResponse:
    return UserResponse.model_validate(user)


# ── Register ───────────────────────────────────────────────────────────────────

async def register_user(
    db: AsyncSession,
    email: str,
    password: str,
    full_name: str | None,
) -> tuple[User, str]:
    """Create user + free subscription. Returns (user, verification_token)."""
    result = await db.execute(select(User).where(User.email == email.lower()))
    if result.scalar_one_or_none():
        raise ConflictException("An account with this email already exists")

    user = User(
        email=email.lower(),
        hashed_password=hash_password(password),
        full_name=full_name,
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    await db.flush()  # get user.id without committing

    # Create free subscription
    subscription = Subscription(
        user_id=user.id,
        plan=PlanType.FREE,
        status=SubscriptionStatus.ACTIVE,
        tokens_limit=settings.FREE_PLAN_TOKENS,
    )
    db.add(subscription)

    verification_token = secrets.token_urlsafe(32)
    return user, verification_token


# ── Login ──────────────────────────────────────────────────────────────────────

async def login_user(
    db: AsyncSession,
    redis: aioredis.Redis,
    email: str,
    password: str,
    ip: str,
) -> tuple[User, str, str]:
    """Authenticate user. Returns (user, access_token, refresh_token)."""
    rate_key = f"login_attempts:{ip}"
    attempts = await redis.get(rate_key)
    if attempts and int(attempts) >= 5:
        raise BadRequestException("Too many login attempts. Please wait 15 minutes.")

    result = await db.execute(select(User).where(User.email == email.lower()))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.hashed_password):
        pipe = redis.pipeline()
        pipe.incr(rate_key)
        pipe.expire(rate_key, 900)  # 15 min TTL
        await pipe.execute()
        raise UnauthorizedException("Invalid email or password")

    if not user.is_active:
        raise BadRequestException("Account is disabled. Please contact support.")

    await redis.delete(rate_key)

    access_token = create_access_token(str(user.id))
    refresh_token_str = create_refresh_token(str(user.id))

    rt = RefreshToken(
        user_id=user.id,
        token_hash=_hash_token(refresh_token_str),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(rt)

    return user, access_token, refresh_token_str


# ── Refresh ────────────────────────────────────────────────────────────────────

async def refresh_access_token(
    db: AsyncSession,
    refresh_token_str: str,
) -> tuple[User, str]:
    """Validate refresh token cookie, issue new access token."""
    try:
        payload = decode_token(refresh_token_str)
    except ValueError:
        raise UnauthorizedException("Invalid refresh token")

    if payload.get("type") != "refresh":
        raise UnauthorizedException("Invalid token type")

    token_hash = _hash_token(refresh_token_str)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    rt = result.scalar_one_or_none()

    if not rt or not rt.is_valid:
        raise UnauthorizedException("Refresh token expired or revoked")

    user_result = await db.execute(select(User).where(User.id == rt.user_id))
    user = user_result.scalar_one_or_none()
    if not user or not user.is_active:
        raise UnauthorizedException("User not found or inactive")

    new_access_token = create_access_token(str(user.id))
    return user, new_access_token


# ── Logout ─────────────────────────────────────────────────────────────────────

async def logout_user(db: AsyncSession, refresh_token_str: str) -> None:
    """Revoke the refresh token."""
    if not refresh_token_str:
        return
    token_hash = _hash_token(refresh_token_str)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    rt = result.scalar_one_or_none()
    if rt:
        rt.revoked = True


# ── Get current user ───────────────────────────────────────────────────────────

async def get_current_user(db: AsyncSession, token: str) -> User:
    """Decode access token and return the user."""
    try:
        payload = decode_token(token)
    except ValueError:
        raise UnauthorizedException("Invalid access token")

    if payload.get("type") != "access":
        raise UnauthorizedException("Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedException("Invalid token payload")

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise UnauthorizedException("User not found or inactive")

    return user


# ── Email verification ─────────────────────────────────────────────────────────

async def store_verification_token(
    redis: aioredis.Redis, user_id: str, token: str
) -> None:
    await redis.setex(f"verify_email:{token}", 86400, user_id)


async def verify_email_token(
    db: AsyncSession, redis: aioredis.Redis, token: str
) -> User:
    user_id = await redis.get(f"verify_email:{token}")
    if not user_id:
        raise BadRequestException("Invalid or expired verification link")

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise BadRequestException("User not found")

    user.is_verified = True
    await redis.delete(f"verify_email:{token}")
    return user


# ── Password reset ─────────────────────────────────────────────────────────────

async def store_password_reset_token(
    redis: aioredis.Redis, user_id: str, token: str
) -> None:
    await redis.setex(f"reset_password:{token}", 3600, user_id)


async def reset_password(
    db: AsyncSession, redis: aioredis.Redis, token: str, new_password: str
) -> None:
    user_id = await redis.get(f"reset_password:{token}")
    if not user_id:
        raise BadRequestException("Invalid or expired reset link")

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise BadRequestException("User not found")

    user.hashed_password = hash_password(new_password)
    await redis.delete(f"reset_password:{token}")

    # Revoke all existing refresh tokens for security
    from sqlalchemy import update as sa_update
    await db.execute(
        sa_update(RefreshToken)
        .where(RefreshToken.user_id == user.id)
        .values(revoked=True)
    )
