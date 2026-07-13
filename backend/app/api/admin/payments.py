from __future__ import annotations

from datetime import date, datetime, time, timezone
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, model_validator
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.api.admin.dependencies import get_admin_tenant_context
from app.api.admin.resources import serialize_payment_evidence, serialize_payment_review
from app.db.session import get_db_session
from app.models.tenant import Booking, Location, Organization, Patient, PaymentAttempt, PaymentEvidence, PaymentReview, Practitioner, PractitionerService, Room
from app.services.errors import BusinessRuleViolation, DomainValidationError, ResourceNotFound
from app.tenancy.context import TenantContext

router = APIRouter(prefix="/payments", tags=["admin-payments"])
REVIEWABLE_STATUSES = {"evidence_received", "under_review"}
PAY_ON_SITE_REVIEWABLE_STATUSES = REVIEWABLE_STATUSES | {"pending"}
PAYMENT_STATUSES = {"pending", "evidence_required", "evidence_received", "under_review", "approved", "rejected", "expired", "cancelled", "simulated_approved"}
PAYMENT_METHODS = {"transfer", "simulated", "pay_on_site"}

class RejectPaymentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason: str | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def require_reason(self) -> "RejectPaymentRequest":
        if not (self.reason or self.notes or "").strip():
            raise ValueError("Rejecting a payment requires reason or notes.")
        return self

class ApprovePaymentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    notes: str | None = None


def _amount(value):
    return float(value) if value is not None else None


def _booking_names(session: Session, booking: Booking) -> dict[str, object]:
    org = session.get(Organization, booking.organization_id) if booking.organization_id else None
    loc = session.get(Location, booking.location_id) if booking.location_id else None
    room = session.get(Room, booking.room_id) if booking.room_id else None
    patient = session.get(Patient, booking.patient_id) if booking.patient_id else None
    practitioner = session.get(Practitioner, booking.practitioner_id) if booking.practitioner_id else None
    service = session.get(PractitionerService, booking.practitioner_service_id) if booking.practitioner_service_id else None
    return {
        "organization_id": str(booking.organization_id) if booking.organization_id else None,
        "organization_name": org.name if org else None,
        "location_id": str(booking.location_id) if booking.location_id else None,
        "location_name": loc.name if loc else booking.location_name_snapshot,
        "room_id": str(booking.room_id) if booking.room_id else None,
        "room_name": room.name if room else booking.room_snapshot,
        "patient_id": str(booking.patient_id) if booking.patient_id else None,
        "patient_name": patient.full_name if patient else None,
        "practitioner_id": str(booking.practitioner_id) if booking.practitioner_id else None,
        "practitioner_name": practitioner.full_name if practitioner else booking.practitioner_name_snapshot,
        "practitioner_service_id": str(booking.practitioner_service_id) if booking.practitioner_service_id else None,
        "practitioner_service_name": service.name if service else booking.service_name_snapshot,
        "appointment_starts_at": booking.starts_at.isoformat() if booking.starts_at else None,
        "appointment_ends_at": booking.ends_at.isoformat() if booking.ends_at else None,
        "booking_status": booking.status,
        "booking_payment_status": booking.payment_status,
        "booking_notes": getattr(booking, "notes", None),
    }


def serialize_admin_payment(attempt: PaymentAttempt, session: Session, *, include_children: bool = False) -> dict[str, object]:
    booking = attempt.booking or session.get(Booking, attempt.booking_id)
    if booking is None:
        raise ResourceNotFound("Booking not found for payment attempt.")
    latest_review = max(attempt.reviews, key=lambda r: r.reviewed_at) if attempt.reviews else None
    data = {
        "id": str(attempt.id),
        "booking_id": str(attempt.booking_id),
        "method": attempt.method,
        "status": attempt.status,
        "amount": _amount(attempt.amount),
        "currency": attempt.currency,
        "expires_at": attempt.expires_at.isoformat() if attempt.expires_at else None,
        "evidence_received_at": attempt.evidence_received_at.isoformat() if attempt.evidence_received_at else None,
        "reviewed_at": attempt.reviewed_at.isoformat() if attempt.reviewed_at else None,
        "evidence_count": len(attempt.evidence),
        "latest_review_decision": latest_review.decision if latest_review else None,
        **_booking_names(session, booking),
    }
    if include_children:
        data["evidence"] = [serialize_payment_evidence(item) for item in sorted(attempt.evidence, key=lambda e: e.uploaded_at)]
        data["reviews"] = [serialize_payment_review(item) for item in sorted(attempt.reviews, key=lambda r: r.reviewed_at)]
    return data


def _base_query():
    return select(PaymentAttempt).options(selectinload(PaymentAttempt.booking), selectinload(PaymentAttempt.evidence), selectinload(PaymentAttempt.reviews)).join(Booking, PaymentAttempt.booking_id == Booking.id)

@router.get("")
def list_payments(organization_id: UUID | None = None, status: str | None = None, method: str | None = None, date_from: date | None = None, date_to: date | None = None, patient: str | None = None, booking_id: UUID | None = None, practitioner_id: UUID | None = None, tenant_context: TenantContext = Depends(get_admin_tenant_context), session: Session = Depends(get_db_session)):
    _ = tenant_context
    if status and status not in PAYMENT_STATUSES: raise DomainValidationError("Invalid payment status.")
    if method and method not in PAYMENT_METHODS: raise DomainValidationError("Invalid payment method.")
    stmt = _base_query().outerjoin(Patient, Booking.patient_id == Patient.id)
    if organization_id: stmt = stmt.where(Booking.organization_id == organization_id)
    if status: stmt = stmt.where(PaymentAttempt.status == status)
    if method: stmt = stmt.where(PaymentAttempt.method == method)
    if booking_id: stmt = stmt.where(PaymentAttempt.booking_id == booking_id)
    if practitioner_id: stmt = stmt.where(Booking.practitioner_id == practitioner_id)
    if date_from: stmt = stmt.where(Booking.starts_at >= datetime.combine(date_from, time.min))
    if date_to: stmt = stmt.where(Booking.starts_at <= datetime.combine(date_to, time.max))
    if patient:
        needle = f"%{patient.strip().lower()}%"
        stmt = stmt.where(or_(func.lower(Patient.full_name).like(needle), func.lower(Patient.document_number).like(needle)))
    rows = session.scalars(stmt.order_by(Booking.starts_at.desc(), PaymentAttempt.id)).unique().all()
    return {"data": [serialize_admin_payment(row, session) for row in rows]}

@router.get("/{payment_attempt_id}")
def get_payment(payment_attempt_id: UUID, tenant_context: TenantContext = Depends(get_admin_tenant_context), session: Session = Depends(get_db_session)):
    _ = tenant_context
    attempt = session.scalars(_base_query().where(PaymentAttempt.id == payment_attempt_id)).unique().first()
    if attempt is None: raise ResourceNotFound("Payment attempt not found.")
    return {"data": serialize_admin_payment(attempt, session, include_children=True)}


def _assert_reviewable(attempt: PaymentAttempt) -> None:
    allowed = PAY_ON_SITE_REVIEWABLE_STATUSES if attempt.method == "pay_on_site" else REVIEWABLE_STATUSES
    if attempt.status not in allowed:
        raise BusinessRuleViolation("Payment attempt is not in a manually reviewable status.")


def _review(payment_attempt_id: UUID, decision: str, notes: str | None, session: Session):
    attempt = session.scalars(_base_query().where(PaymentAttempt.id == payment_attempt_id)).unique().first()
    if attempt is None: raise ResourceNotFound("Payment attempt not found.")
    _assert_reviewable(attempt)
    now = datetime.now(timezone.utc)
    attempt.status = "approved" if decision == "approved" else "rejected"
    attempt.reviewed_at = now
    if attempt.booking:
        attempt.booking.payment_status = "paid" if decision == "approved" else "rejected"
    review = PaymentReview(payment_attempt_id=attempt.id, decision=decision, reviewed_at=now, notes=notes)
    attempt.reviews.append(review)
    try:
        session.add(review); session.flush(); data = serialize_admin_payment(attempt, session, include_children=True); session.commit()
    except Exception:
        session.rollback(); raise
    return {"data": data}

@router.post("/{payment_attempt_id}/approve")
def approve_payment(payment_attempt_id: UUID, payload: ApprovePaymentRequest, tenant_context: TenantContext = Depends(get_admin_tenant_context), session: Session = Depends(get_db_session)):
    _ = tenant_context
    return _review(payment_attempt_id, "approved", payload.notes, session)

@router.post("/{payment_attempt_id}/reject")
def reject_payment(payment_attempt_id: UUID, payload: RejectPaymentRequest, tenant_context: TenantContext = Depends(get_admin_tenant_context), session: Session = Depends(get_db_session)):
    _ = tenant_context
    return _review(payment_attempt_id, "rejected", payload.reason or payload.notes, session)
