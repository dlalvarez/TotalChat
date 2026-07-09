from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tenant import Booking, PaymentAttempt, PaymentEvidence, PaymentSettings
from app.services.errors import BusinessRuleViolation, DomainValidationError, ResourceNotFound
from app.tenancy.context import TenantContext

PAYMENT_ATTEMPT_METHODS = {"transfer", "simulated", "pay_on_site"}
EVIDENCE_REGISTRATION_STATUSES = {"evidence_required"}

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



class PaymentEvidenceService:
    """Backend-owned transfer evidence registration rules for Spec 007 PR 23."""

    def __init__(self, session: Session, tenant_context: TenantContext):
        if tenant_context is None:
            raise DomainValidationError("PaymentEvidenceService requires explicit TenantContext")
        self.session = session
        self.tenant_context = tenant_context

    def register_evidence(
        self,
        *,
        payment_attempt_id: UUID,
        storage_object_key: str | None = None,
        original_filename: str | None = None,
        content_type: str | None = None,
        uploaded_channel: str | None = None,
        notes: str | None = None,
    ) -> PaymentEvidence:
        attempt = self.session.get(PaymentAttempt, payment_attempt_id)
        if attempt is None:
            raise ResourceNotFound("Payment attempt not found.")
        if attempt.method != "transfer":
            raise BusinessRuleViolation("Evidence can only be registered for transfer payment attempts.")
        if attempt.status not in EVIDENCE_REGISTRATION_STATUSES:
            raise BusinessRuleViolation("Payment attempt status does not allow evidence registration.")

        received_at = datetime.now(timezone.utc)
        evidence = PaymentEvidence(
            payment_attempt_id=attempt.id,
            storage_object_key=storage_object_key,
            original_filename=original_filename,
            content_type=content_type,
            uploaded_at=received_at,
            uploaded_channel=uploaded_channel,
            notes=notes,
        )
        if attempt.evidence_received_at is None:
            attempt.evidence_received_at = received_at
        attempt.status = "evidence_received"
        self.session.add(evidence)
        return evidence
