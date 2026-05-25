import uuid
from pydantic import BaseModel
from app.models.subscription import PlanType, SubscriptionStatus


class SubscriptionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    plan: PlanType
    status: SubscriptionStatus
    tokens_used: int
    tokens_limit: int
    tokens_remaining: int
    is_quota_exceeded: bool
    stripe_customer_id: str | None
    stripe_subscription_id: str | None

    model_config = {"from_attributes": True}


class CheckoutSessionResponse(BaseModel):
    checkout_url: str


class BillingPortalResponse(BaseModel):
    portal_url: str


class PlanInfo(BaseModel):
    plan: PlanType
    name: str
    price_monthly: float
    tokens_per_month: int
    features: list[str]
    stripe_price_id: str
