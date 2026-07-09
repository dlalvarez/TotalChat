from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tenant import Booking, PaymentAttempt, PaymentEvidence, PaymentReview, PaymentSettings
from app.services.booking import BookingTransitionService
from app.services.errors import BusinessRuleViolation, DomainValidationError, ResourceNotFound
from app.tenancy.context import TenantContext

PAYMENT_ATTEMPT_METHODS = {"transfer", "simulated", "pay_on_site"}
EVIDENCE_REGISTRATION_STATUSES = {"evidence_required"}
PAYMENT_REVIEW_DECISIONS = {"approved", "rejected"}
PAYMENT_REVIEW_ALLOWED_STATUSES = {"evidence_received"}

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


class PaymentReviewService:
    """Backend-owned manual administrative payment review rules for Spec 007 PR 24."""

    def __init__(self, session: Session, tenant_context: TenantContext):
        if tenant_context is None:
            raise DomainValidationError("PaymentReviewService requires explicit TenantContext")
        self.session = session
        self.tenant_context = tenant_context

    def approve_attempt(
        self,
        *,
        payment_attempt_id: UUID,
        reviewer_user_id: UUID | None = None,
        notes: str | None = None,
    ) -> PaymentReview:
        return self._review_attempt(
            payment_attempt_id=payment_attempt_id,
            decision="approved",
            reviewer_user_id=reviewer_user_id,
            notes=notes,
        )

    def reject_attempt(
        self,
        *,
        payment_attempt_id: UUID,
        reviewer_user_id: UUID | None = None,
        notes: str | None = None,
    ) -> PaymentReview:
        return self._review_attempt(
            payment_attempt_id=payment_attempt_id,
            decision="rejected",
            reviewer_user_id=reviewer_user_id,
            notes=notes,
        )

    def _review_attempt(
        self,
        *,
        payment_attempt_id: UUID,
        decision: str,
        reviewer_user_id: UUID | None,
        notes: str | None,
    ) -> PaymentReview:
        if decision not in PAYMENT_REVIEW_DECISIONS:
            raise DomainValidationError("Payment review decision must be approved or rejected.")
        attempt = self.session.get(PaymentAttempt, payment_attempt_id)
        if attempt is None:
            raise ResourceNotFound("Payment attempt not found.")
        if attempt.method != "transfer":
            raise BusinessRuleViolation("Manual review is only allowed for transfer payment attempts.")
        if attempt.status not in PAYMENT_REVIEW_ALLOWED_STATUSES:
            raise BusinessRuleViolation("Payment attempt status does not allow manual review.")

        reviewed_at = datetime.now(timezone.utc)
        review = PaymentReview(
            payment_attempt_id=attempt.id,
            decision=decision,
            reviewer_user_id=reviewer_user_id,
            reviewed_at=reviewed_at,
            notes=notes,
        )
        attempt.status = decision
        attempt.reviewed_at = reviewed_at
        attempt.reviewed_by_user_id = reviewer_user_id
        self.session.add(review)
        return review


@dataclass(frozen=True, slots=True)
class PaymentExpiryResult:
    payment_attempt: PaymentAttempt
    action: str
    booking_action: str


class PaymentExpiryService:
    """Backend-owned expiry and review-overdue rules for Spec 007 PR 25."""

    def __init__(self, session: Session, tenant_context: TenantContext):
        if tenant_context is None:
            raise DomainValidationError("PaymentExpiryService requires explicit TenantContext")
        self.session = session
        self.tenant_context = tenant_context
        self.booking_transition_service = BookingTransitionService()

    def expire_missing_evidence(
        self,
        *,
        payment_attempt_id: UUID,
        force: bool = False,
        notes: str | None = None,
    ) -> PaymentExpiryResult:
        attempt = self._get_transfer_attempt(
            payment_attempt_id=payment_attempt_id,
            required_status="evidence_required",
        )
        now = datetime.now(timezone.utc)
        expires_at = self._as_aware(attempt.expires_at)
        if not force and (expires_at is None or expires_at > now):
            raise BusinessRuleViolation("Payment attempt has not reached its missing-evidence expiry deadline.")

        attempt.status = "expired"
        settings = self._active_settings_for_attempt(attempt)
        booking_action = self._apply_release_policy(
            attempt=attempt,
            should_release=bool(settings and settings.release_slot_on_missing_evidence),
            reason=notes or "Payment attempt expired without evidence.",
        )
        return PaymentExpiryResult(
            payment_attempt=attempt,
            action="expired_missing_evidence",
            booking_action=booking_action,
        )

    def mark_review_overdue(
        self,
        *,
        payment_attempt_id: UUID,
        force: bool = False,
        notes: str | None = None,
    ) -> PaymentExpiryResult:
        attempt = self._get_transfer_attempt(
            payment_attempt_id=payment_attempt_id,
            required_status="evidence_received",
        )
        settings = self._active_settings_for_attempt(attempt)
        if settings is None:
            raise BusinessRuleViolation("Active payment settings are required to evaluate review overdue deadline.")
        now = datetime.now(timezone.utc)
        evidence_received_at = self._as_aware(attempt.evidence_received_at)
        deadline_at = (
            None
            if evidence_received_at is None
            else evidence_received_at + timedelta(minutes=settings.manual_review_deadline_minutes)
        )
        if not force and (deadline_at is None or now < deadline_at):
            raise BusinessRuleViolation("Payment attempt has not reached its manual-review overdue deadline.")

        booking_action = self._apply_release_policy(
            attempt=attempt,
            should_release=settings.release_slot_on_review_overdue,
            reason=notes or "Payment attempt manual review is overdue.",
        )
        return PaymentExpiryResult(
            payment_attempt=attempt,
            action="marked_review_overdue",
            booking_action=booking_action,
        )

    def _get_transfer_attempt(self, *, payment_attempt_id: UUID, required_status: str) -> PaymentAttempt:
        attempt = self.session.get(PaymentAttempt, payment_attempt_id)
        if attempt is None:
            raise ResourceNotFound("Payment attempt not found.")
        if attempt.method != "transfer":
            raise BusinessRuleViolation("Action is only allowed for transfer payment attempts.")
        if attempt.status != required_status:
            raise BusinessRuleViolation("Payment attempt status does not allow this action.")
        return attempt

    def _active_settings_for_attempt(self, attempt: PaymentAttempt) -> PaymentSettings | None:
        booking = attempt.booking or self.session.get(Booking, attempt.booking_id)
        if booking is None:
            raise ResourceNotFound("Booking not found.")
        return self.session.scalar(
            select(PaymentSettings).where(
                PaymentSettings.organization_id == booking.organization_id,
                PaymentSettings.status == "active",
            )
        )

    def _apply_release_policy(self, *, attempt: PaymentAttempt, should_release: bool, reason: str) -> str:
        if not should_release:
            return "not_applied_policy_disabled"
        booking = attempt.booking or self.session.get(Booking, attempt.booking_id)
        if booking is None:
            raise ResourceNotFound("Booking not found.")
        try:
            self.booking_transition_service.transition(booking, "expired_no_evidence")
        except BusinessRuleViolation:
            return "not_applied_no_safe_domain_transition"
        return "released_via_booking_transition_service"

    @staticmethod
    def _as_aware(value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
