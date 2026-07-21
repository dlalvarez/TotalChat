"""Tenant-scoped payment tools for the booking agent."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tenant import Booking, Organization, PaymentAttempt, PaymentSettings
from app.services.errors import BusinessRuleViolation, ResourceNotFound


PAYMENT_METHODS = ("transfer", "simulated", "pay_on_site")
PAYMENT_PREPARABLE_BOOKING_STATUSES = frozenset(
    {
        "tentative",
        "pending_payment",
        "pending_payment_evidence",
        "pending_manual_payment_review",
        "review_overdue",
        "confirmed",
        "confirmed_without_payment",
        "rescheduled",
    }
)


@dataclass(frozen=True, slots=True)
class PaymentStatusRequest:
    booking_id: UUID


@dataclass(frozen=True, slots=True)
class PaymentPreparationRequest:
    booking_id: UUID
    method: str

    def __post_init__(self) -> None:
        if self.method not in PAYMENT_METHODS:
            raise ValueError("method must be transfer, simulated, or pay_on_site")


@dataclass(frozen=True, slots=True)
class PaymentMethodOption:
    method: str
    requires_evidence: bool
    manual_review_required: bool


@dataclass(frozen=True, slots=True)
class PaymentToolResult:
    booking_id: UUID
    booking_status: str
    payment_status: str
    amount: Decimal
    currency: str
    available_methods: tuple[PaymentMethodOption, ...]
    payment_attempt_id: UUID | None
    attempt_status: str | None
    requires_evidence: bool
    manual_review_required: bool


class PaymentRepository(Protocol):
    def get_status(self, request: PaymentStatusRequest) -> PaymentToolResult: ...

    def prepare(self, request: PaymentPreparationRequest) -> PaymentToolResult: ...


class SQLAlchemyPaymentRepository:
    """Payment persistence using an already tenant-scoped session."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_status(self, request: PaymentStatusRequest) -> PaymentToolResult:
        booking = self._booking(request.booking_id)
        return self._result(booking, self._latest_attempt(booking.id))

    def prepare(self, request: PaymentPreparationRequest) -> PaymentToolResult:
        booking = self._booking(request.booking_id)
        if booking.status not in PAYMENT_PREPARABLE_BOOKING_STATUSES:
            raise BusinessRuleViolation("Booking status does not allow payment preparation.")
        options = self._available_methods(booking.organization_id)
        if request.method not in {option.method for option in options}:
            raise BusinessRuleViolation("Payment method is disabled by active payment settings.")

        status = "evidence_required" if request.method == "transfer" else "pending"
        attempt = PaymentAttempt(
            booking_id=booking.id,
            method=request.method,
            amount=booking.total_amount,
            currency=booking.currency_snapshot,
            status=status,
        )
        self._session.add(attempt)
        self._session.flush()
        return self._result(booking, attempt, options)

    def _booking(self, booking_id: UUID) -> Booking:
        booking = self._session.scalar(
            select(Booking)
            .join(Organization, Booking.organization_id == Organization.id)
            .where(Booking.id == booking_id, Organization.status == "active")
        )
        if booking is None:
            raise ResourceNotFound("Booking not found in an active organization.")
        return booking

    def _latest_attempt(self, booking_id: UUID) -> PaymentAttempt | None:
        return self._session.scalar(
            select(PaymentAttempt)
            .where(PaymentAttempt.booking_id == booking_id)
            .order_by(PaymentAttempt.created_at.desc(), PaymentAttempt.id.desc())
            .limit(1)
        )

    def _available_methods(self, organization_id: UUID) -> tuple[PaymentMethodOption, ...]:
        settings = self._session.scalar(
            select(PaymentSettings)
            .where(
                PaymentSettings.organization_id == organization_id,
                PaymentSettings.status == "active",
            )
            .order_by(PaymentSettings.created_at.desc(), PaymentSettings.id.desc())
            .limit(1)
        )
        if settings is None:
            return ()
        allowed = {
            "transfer": settings.allow_transfer,
            "simulated": settings.allow_simulated_payment,
            "pay_on_site": settings.allow_pay_on_site,
        }
        return tuple(
            PaymentMethodOption(
                method=method,
                requires_evidence=method == "transfer",
                manual_review_required=method == "transfer",
            )
            for method in PAYMENT_METHODS
            if allowed[method]
        )

    def _result(
        self,
        booking: Booking,
        attempt: PaymentAttempt | None,
        options: tuple[PaymentMethodOption, ...] | None = None,
    ) -> PaymentToolResult:
        attempt_status = attempt.status if attempt is not None else None
        transfer = attempt is not None and attempt.method == "transfer"
        return PaymentToolResult(
            booking_id=booking.id,
            booking_status=booking.status,
            payment_status=booking.payment_status,
            amount=booking.total_amount,
            currency=booking.currency_snapshot,
            available_methods=options if options is not None else self._available_methods(booking.organization_id),
            payment_attempt_id=attempt.id if attempt is not None else None,
            attempt_status=attempt_status,
            requires_evidence=transfer and attempt_status == "evidence_required",
            manual_review_required=transfer and attempt_status in {"evidence_received", "under_review"},
        )


class PaymentTools:
    """Structured payment operations for an already-resolved tenant."""

    def __init__(
        self,
        *,
        tenant_id: UUID,
        repository: PaymentRepository | None = None,
        session: Session | None = None,
    ) -> None:
        if not isinstance(tenant_id, UUID):
            raise TypeError("tenant_id must be a backend-resolved UUID")
        if repository is None and session is None:
            raise ValueError("a tenant-scoped repository or session is required")
        if repository is not None and session is not None:
            raise ValueError("provide repository or session, not both")
        self._tenant_id = tenant_id
        self._repository = repository or SQLAlchemyPaymentRepository(session)  # type: ignore[arg-type]

    def get_payment_status(self, request: PaymentStatusRequest) -> PaymentToolResult:
        return self._repository.get_status(request)

    def prepare_payment(self, request: PaymentPreparationRequest) -> PaymentToolResult:
        return self._repository.prepare(request)
