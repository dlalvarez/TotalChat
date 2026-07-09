from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tenant import Booking, PaymentAttempt, PaymentSettings
from app.services.errors import BusinessRuleViolation, DomainValidationError, ResourceNotFound
from app.tenancy.context import TenantContext

PAYMENT_ATTEMPT_METHODS = {"transfer", "simulated", "pay_on_site"}
PAYMENT_ATTEMPT_STATUSES = {
    "pending",
    "evidence_required",
    "evidence_received",
    "under_review",
    "approved",
    "rejected",
    "expired",
    "cancelled",
    "simulated_approved",
}

_METHOD_STATUS = {
    "transfer": "evidence_required",
    "simulated": "simulated_approved",
    "pay_on_site": "pending",
}


class PaymentAttemptService:
    """Backend-owned payment attempt creation rules for Spec 007 PR 22."""

    def __init__(self, session: Session, tenant_context: TenantContext):
        if tenant_context is None:
            raise DomainValidationError("PaymentAttemptService requires explicit TenantContext")
        self.session = session
        self.tenant_context = tenant_context

    def create_attempt(
        self,
        *,
        booking_id: UUID,
        method: str,
        amount: Decimal,
        currency: str,
        expires_at: datetime | None = None,
    ) -> PaymentAttempt:
        if method not in PAYMENT_ATTEMPT_METHODS:
            raise DomainValidationError("Unsupported payment method.")
        if amount < 0:
            raise DomainValidationError("amount must be greater than or equal to 0")
        if len(currency) != 3 or not currency.isalpha() or currency.upper() != currency:
            raise DomainValidationError("currency must be a 3-letter uppercase code")

        booking = self.session.get(Booking, booking_id)
        if booking is None:
            raise ResourceNotFound("Booking not found.")

        self._ensure_method_allowed(booking, method)
        attempt = PaymentAttempt(
            booking_id=booking.id,
            method=method,
            amount=amount,
            currency=currency,
            status=_METHOD_STATUS[method],
            expires_at=expires_at,
        )
        self.session.add(attempt)
        return attempt

    def _ensure_method_allowed(self, booking: Booking, method: str) -> None:
        settings = self.session.scalar(
            select(PaymentSettings).where(
                PaymentSettings.organization_id == booking.organization_id,
                PaymentSettings.status == "active",
            )
        )
        if settings is None:
            return
        allowed_by_method = {
            "transfer": settings.allow_transfer,
            "simulated": settings.allow_simulated_payment,
            "pay_on_site": settings.allow_pay_on_site,
        }
        if not allowed_by_method[method]:
            raise BusinessRuleViolation("Payment method is disabled by active payment settings.")
