"""
Billing service — Stripe Checkout, webhooks, portal, token quota enforcement.
"""
import stripe
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import BadRequestException, NotFoundException
from app.models.subscription import PlanType, Subscription, SubscriptionStatus
from app.models.user import User
from app.schemas.billing import PlanInfo

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

# ── Plan catalogue ─────────────────────────────────────────────────────────────

PLANS: dict[PlanType, PlanInfo] = {
    PlanType.FREE: PlanInfo(
        plan=PlanType.FREE,
        name="Free",
        price_monthly=0.0,
        tokens_per_month=50_000,
        stripe_price_id="",
        features=[
            "50,000 tokens / month",
            "AI chatbot",
            "3 document uploads",
            "Basic AI search",
        ],
    ),
    PlanType.PRO: PlanInfo(
        plan=PlanType.PRO,
        name="Pro",
        price_monthly=19.0,
        tokens_per_month=500_000,
        stripe_price_id=settings.STRIPE_PRO_PRICE_ID,
        features=[
            "500,000 tokens / month",
            "All AI features",
            "50 document uploads",
            "AI summarization",
            "Meeting notes & task planner",
            "Voice transcription",
            "Priority support",
        ],
    ),
    PlanType.TEAM: PlanInfo(
        plan=PlanType.TEAM,
        name="Team",
        price_monthly=49.0,
        tokens_per_month=2_000_000,
        stripe_price_id=settings.STRIPE_TEAM_PRICE_ID,
        features=[
            "2,000,000 tokens / month",
            "Everything in Pro",
            "Team workspaces",
            "Real-time collaboration",
            "Admin analytics dashboard",
            "API access",
            "Dedicated support",
        ],
    ),
}

TOKEN_LIMITS: dict[PlanType, int] = {
    PlanType.FREE: settings.FREE_PLAN_TOKENS,
    PlanType.PRO: settings.PRO_PLAN_TOKENS,
    PlanType.TEAM: settings.TEAM_PLAN_TOKENS,
}


# ── Subscription helpers ───────────────────────────────────────────────────────

async def get_subscription(db: AsyncSession, user_id) -> Subscription:
    result = await db.execute(
        select(Subscription).where(Subscription.user_id == user_id)
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise NotFoundException("Subscription not found")
    return sub


async def deduct_tokens(db: AsyncSession, user_id, tokens: int) -> Subscription:
    """Deduct tokens from user quota. Raises QuotaExceededException if over limit."""
    from app.core.exceptions import QuotaExceededException
    sub = await get_subscription(db, user_id)
    if sub.tokens_used + tokens > sub.tokens_limit:
        raise QuotaExceededException()
    sub.tokens_used += tokens
    return sub


# ── Stripe Checkout ────────────────────────────────────────────────────────────

async def create_checkout_session(
    db: AsyncSession,
    user: User,
    plan: PlanType,
    success_url: str,
    cancel_url: str,
) -> str:
    """Create a Stripe Checkout session and return the URL."""
    if not settings.STRIPE_SECRET_KEY:
        raise BadRequestException("Stripe is not configured")

    plan_info = PLANS.get(plan)
    if not plan_info or not plan_info.stripe_price_id:
        raise BadRequestException(f"No Stripe price configured for plan: {plan}")

    sub = await get_subscription(db, user.id)

    # Get or create Stripe customer
    customer_id = sub.stripe_customer_id
    if not customer_id:
        customer = stripe.Customer.create(
            email=user.email,
            name=user.full_name or user.email,
            metadata={"user_id": str(user.id)},
        )
        customer_id = customer.id
        sub.stripe_customer_id = customer_id

    session = stripe.checkout.Session.create(
        customer=customer_id,
        payment_method_types=["card"],
        line_items=[{"price": plan_info.stripe_price_id, "quantity": 1}],
        mode="subscription",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"user_id": str(user.id), "plan": plan.value},
    )
    return session.url


# ── Stripe Customer Portal ─────────────────────────────────────────────────────

async def create_portal_session(db: AsyncSession, user: User, return_url: str) -> str:
    """Create a Stripe billing portal session."""
    if not settings.STRIPE_SECRET_KEY:
        raise BadRequestException("Stripe is not configured")

    sub = await get_subscription(db, user.id)
    if not sub.stripe_customer_id:
        raise BadRequestException("No billing account found. Please subscribe first.")

    session = stripe.billing_portal.Session.create(
        customer=sub.stripe_customer_id,
        return_url=return_url,
    )
    return session.url


# ── Stripe Webhook handler ─────────────────────────────────────────────────────

async def handle_stripe_webhook(db: AsyncSession, payload: bytes, sig_header: str) -> dict:
    """Verify and process Stripe webhook events."""
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        raise BadRequestException("Invalid Stripe webhook signature")

    event_type = event["type"]
    data = event["data"]["object"]

    if event_type == "checkout.session.completed":
        await _handle_checkout_completed(db, data)

    elif event_type in ("invoice.paid", "invoice.payment_succeeded"):
        await _handle_invoice_paid(db, data)

    elif event_type in ("customer.subscription.deleted", "customer.subscription.updated"):
        await _handle_subscription_updated(db, data)

    return {"received": True}


async def _handle_checkout_completed(db: AsyncSession, session: dict) -> None:
    user_id = session.get("metadata", {}).get("user_id")
    plan_str = session.get("metadata", {}).get("plan")
    stripe_sub_id = session.get("subscription")

    if not user_id or not plan_str:
        return

    result = await db.execute(
        select(Subscription).where(Subscription.user_id == user_id)
    )
    sub = result.scalar_one_or_none()
    if not sub:
        return

    try:
        plan = PlanType(plan_str)
    except ValueError:
        return

    sub.plan = plan
    sub.status = SubscriptionStatus.ACTIVE
    sub.stripe_subscription_id = stripe_sub_id
    sub.tokens_limit = TOKEN_LIMITS[plan]


async def _handle_invoice_paid(db: AsyncSession, invoice: dict) -> None:
    stripe_sub_id = invoice.get("subscription")
    if not stripe_sub_id:
        return

    result = await db.execute(
        select(Subscription).where(Subscription.stripe_subscription_id == stripe_sub_id)
    )
    sub = result.scalar_one_or_none()
    if sub:
        sub.status = SubscriptionStatus.ACTIVE
        sub.tokens_used = 0  # Reset monthly tokens on successful payment


async def _handle_subscription_updated(db: AsyncSession, stripe_sub: dict) -> None:
    stripe_sub_id = stripe_sub.get("id")
    stripe_status = stripe_sub.get("status")

    result = await db.execute(
        select(Subscription).where(Subscription.stripe_subscription_id == stripe_sub_id)
    )
    sub = result.scalar_one_or_none()
    if not sub:
        return

    status_map = {
        "active": SubscriptionStatus.ACTIVE,
        "canceled": SubscriptionStatus.CANCELED,
        "past_due": SubscriptionStatus.PAST_DUE,
        "trialing": SubscriptionStatus.TRIALING,
    }
    if stripe_status in status_map:
        sub.status = status_map[stripe_status]

    if stripe_status == "canceled":
        sub.plan = PlanType.FREE
        sub.tokens_limit = TOKEN_LIMITS[PlanType.FREE]
