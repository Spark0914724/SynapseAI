"""
Billing endpoints — plans, checkout, portal, webhook, subscription status.
"""
from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.models.subscription import PlanType
from app.models.user import User
from app.schemas.billing import (
    BillingPortalResponse,
    CheckoutSessionResponse,
    PlanInfo,
    SubscriptionResponse,
)
from app.services import billing_service

router = APIRouter(prefix="/billing", tags=["billing"])

FRONTEND_URL = "http://localhost:5173"


# ── Plans catalogue ────────────────────────────────────────────────────────────

@router.get("/plans", response_model=list[PlanInfo])
async def list_plans():
    """Return all available subscription plans."""
    return list(billing_service.PLANS.values())


# ── Current subscription ───────────────────────────────────────────────────────

@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    sub = await billing_service.get_subscription(db, current_user.id)
    return SubscriptionResponse(
        id=sub.id,
        user_id=sub.user_id,
        plan=sub.plan,
        status=sub.status,
        tokens_used=sub.tokens_used,
        tokens_limit=sub.tokens_limit,
        tokens_remaining=sub.tokens_remaining,
        is_quota_exceeded=sub.is_quota_exceeded,
        stripe_customer_id=sub.stripe_customer_id,
        stripe_subscription_id=sub.stripe_subscription_id,
    )


# ── Checkout ───────────────────────────────────────────────────────────────────

@router.post("/checkout/{plan}", response_model=CheckoutSessionResponse)
async def create_checkout(
    plan: PlanType,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    url = await billing_service.create_checkout_session(
        db,
        current_user,
        plan,
        success_url=f"{FRONTEND_URL}/app/settings?tab=billing&success=1",
        cancel_url=f"{FRONTEND_URL}/app/settings?tab=billing&canceled=1",
    )
    return CheckoutSessionResponse(checkout_url=url)


# ── Customer portal ────────────────────────────────────────────────────────────

@router.post("/portal", response_model=BillingPortalResponse)
async def billing_portal(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    url = await billing_service.create_portal_session(
        db,
        current_user,
        return_url=f"{FRONTEND_URL}/app/settings?tab=billing",
    )
    return BillingPortalResponse(portal_url=url)


# ── Stripe webhook ─────────────────────────────────────────────────────────────

@router.post("/webhook", include_in_schema=False)
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    stripe_signature: str | None = Header(default=None, alias="stripe-signature"),
):
    payload = await request.body()
    result = await billing_service.handle_stripe_webhook(
        db, payload, stripe_signature or ""
    )
    return result
