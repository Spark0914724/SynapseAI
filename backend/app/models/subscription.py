import uuid
import enum
from sqlalchemy import String, Integer, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin


class PlanType(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    TEAM = "team"


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    TRIALING = "trialing"


class Subscription(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "subscriptions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    plan: Mapped[PlanType] = mapped_column(
        SAEnum(PlanType), default=PlanType.FREE, nullable=False
    )
    status: Mapped[SubscriptionStatus] = mapped_column(
        SAEnum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE, nullable=False
    )
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Token tracking
    tokens_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tokens_limit: Mapped[int] = mapped_column(Integer, default=50_000, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="subscription")  # noqa: F821

    @property
    def tokens_remaining(self) -> int:
        return max(0, self.tokens_limit - self.tokens_used)

    @property
    def is_quota_exceeded(self) -> bool:
        return self.tokens_used >= self.tokens_limit

    def __repr__(self) -> str:
        return f"<Subscription user={self.user_id} plan={self.plan}>"
