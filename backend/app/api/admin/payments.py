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
from app.models.tenant import Booking, Location, Organization, Patient, PaymentAttempt, Practitioner, PractitionerService, Room
from app.services.errors import DomainValidationError, ResourceNotFound
from app.services.payments import PAYMENT_ATTEMPT_METHODS, PAYMENT_ATTEMPT_STATUSES, PaymentReviewService
from app.tenancy.context import TenantContext

router = APIRouter(prefix="/payments", tags=["admin-payments"])


class ApprovePaymentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reviewer_user_id: UUID | None = None
    notes: str | None = None


class RejectPaymentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reviewer_user_id: UUID | None = None
    reason: str | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def require_reason(self) -> "RejectPaymentRequest":
        if not (self.reason or self.notes or "").strip():
            raise ValueError("Rejecting a payment requires reason or notes.")
        return self


def _amount(value):
    return float(value) if value is not None else None


def _ids(values):
    return {value for value in values if value is not None}


def _map_by_id(session: Session, model, ids):
    ids = _ids(ids)
    if not ids:
        return {}
    return {row.id: row for row in session.scalars(select(model).where(model.id.in_(ids))).all()}


def _build_booking_lookups(session: Session, bookings: list[Booking]) -> dict[str, dict[UUID, object]]:
    return {
        "organizations": _map_by_id(session, Organization, [booking.organization_id for booking in bookings]),
        "locations": _map_by_id(session, Location, [booking.location_id for booking in bookings]),
        "rooms": _map_by_id(session, Room, [booking.room_id for booking in bookings]),
        "patients": _map_by_id(session, Patient, [booking.patient_id for booking in bookings]),
        "practitioners": _map_by_id(session, Practitioner, [booking.practitioner_id for booking in bookings]),
        "services": _map_by_id(session, PractitionerService, [booking.practitioner_service_id for booking in bookings]),
    }


def _booking_names(booking: Booking, lookups: dict[str, dict[UUID, object]] | None = None) -> dict[str, object]:
    lookups = lookups or {}
    org = lookups.get("organizations", {}).get(booking.organization_id)
    loc = lookups.get("locations", {}).get(booking.location_id) if booking.location_id else None
    room = lookups.get("rooms", {}).get(booking.room_id) if booking.room_id else None
    patient = lookups.get("patients", {}).get(booking.patient_id)
    practitioner = lookups.get("practitioners", {}).get(booking.practitioner_id)
    service = lookups.get("services", {}).get(booking.practitioner_service_id)
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


def serialize_admin_payment(attempt: PaymentAttempt, *, include_children: bool = False, lookups: dict[str, dict[UUID, object]] | None = None) -> dict[str, object]:
    booking = attempt.booking
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
        "reviewed_by_user_id": str(attempt.reviewed_by_user_id) if attempt.reviewed_by_user_id else None,
        "evidence_count": len(attempt.evidence),
        "latest_review_decision": latest_review.decision if latest_review else None,
        **_booking_names(booking, lookups),
    }
    if include_children:
        data["evidence"] = [serialize_payment_evidence(item) for item in sorted(attempt.evidence, key=lambda e: e.uploaded_at)]
        data["reviews"] = [serialize_payment_review(item) for item in sorted(attempt.reviews, key=lambda r: r.reviewed_at)]
    return data


def _base_query():
    return (
        select(PaymentAttempt)
        .options(selectinload(PaymentAttempt.booking), selectinload(PaymentAttempt.evidence), selectinload(PaymentAttempt.reviews))
        .join(Booking, PaymentAttempt.booking_id == Booking.id)
    )


def _day_start(value: date) -> datetime:
    return datetime.combine(value, time.min, tzinfo=timezone.utc)


def _day_end(value: date) -> datetime:
    return datetime.combine(value, time.max, tzinfo=timezone.utc)


@router.get("")
def list_payments(organization_id: UUID | None = None, status: str | None = None, method: str | None = None, date_from: date | None = None, date_to: date | None = None, patient: str | None = None, booking_id: UUID | None = None, practitioner_id: UUID | None = None, tenant_context: TenantContext = Depends(get_admin_tenant_context), session: Session = Depends(get_db_session)):
    _ = tenant_context
    if status and status not in PAYMENT_ATTEMPT_STATUSES:
        raise DomainValidationError("Invalid payment status.")
    if method and method not in PAYMENT_ATTEMPT_METHODS:
        raise DomainValidationError("Invalid payment method.")
    stmt = _base_query().outerjoin(Patient, Booking.patient_id == Patient.id)
    if organization_id: stmt = stmt.where(Booking.organization_id == organization_id)
    if status: stmt = stmt.where(PaymentAttempt.status == status)
    if method: stmt = stmt.where(PaymentAttempt.method == method)
    if booking_id: stmt = stmt.where(PaymentAttempt.booking_id == booking_id)
    if practitioner_id: stmt = stmt.where(Booking.practitioner_id == practitioner_id)
    if date_from: stmt = stmt.where(Booking.starts_at >= _day_start(date_from))
    if date_to: stmt = stmt.where(Booking.starts_at <= _day_end(date_to))
    if patient:
        needle = f"%{patient.strip().lower()}%"
        stmt = stmt.where(or_(func.lower(Patient.full_name).like(needle), func.lower(Patient.document_number).like(needle)))
    rows = session.scalars(stmt.order_by(Booking.starts_at.desc(), PaymentAttempt.id)).unique().all()
    lookups = _build_booking_lookups(session, [row.booking for row in rows if row.booking is not None])
    return {"data": [serialize_admin_payment(row, lookups=lookups) for row in rows]}


@router.get("/{payment_attempt_id}")
def get_payment(payment_attempt_id: UUID, tenant_context: TenantContext = Depends(get_admin_tenant_context), session: Session = Depends(get_db_session)):
    _ = tenant_context
    attempt = session.scalars(_base_query().where(PaymentAttempt.id == payment_attempt_id)).unique().first()
    if attempt is None: raise ResourceNotFound("Payment attempt not found.")
    lookups = _build_booking_lookups(session, [attempt.booking] if attempt.booking is not None else [])
    return {"data": serialize_admin_payment(attempt, include_children=True, lookups=lookups)}


def _review(payment_attempt_id: UUID, payload: ApprovePaymentRequest | RejectPaymentRequest, decision: str, tenant_context: TenantContext, session: Session):
    try:
        service = PaymentReviewService(session, tenant_context)
        if decision == "approved":
            service.approve_attempt(payment_attempt_id=payment_attempt_id, reviewer_user_id=payload.reviewer_user_id, notes=payload.notes)
        else:
            notes = payload.reason or payload.notes
            service.reject_attempt(payment_attempt_id=payment_attempt_id, reviewer_user_id=payload.reviewer_user_id, notes=notes)
        session.flush()
        attempt = session.scalars(_base_query().where(PaymentAttempt.id == payment_attempt_id)).unique().first()
        if attempt is None: raise ResourceNotFound("Payment attempt not found.")
        lookups = _build_booking_lookups(session, [attempt.booking] if attempt.booking is not None else [])
        data = serialize_admin_payment(attempt, include_children=True, lookups=lookups)
        session.commit()
    except Exception:
        session.rollback(); raise
    return {"data": data}


@router.post("/{payment_attempt_id}/approve")
def approve_payment(payment_attempt_id: UUID, payload: ApprovePaymentRequest, tenant_context: TenantContext = Depends(get_admin_tenant_context), session: Session = Depends(get_db_session)):
    return _review(payment_attempt_id, payload, "approved", tenant_context, session)


@router.post("/{payment_attempt_id}/reject")
def reject_payment(payment_attempt_id: UUID, payload: RejectPaymentRequest, tenant_context: TenantContext = Depends(get_admin_tenant_context), session: Session = Depends(get_db_session)):
    return _review(payment_attempt_id, payload, "rejected", tenant_context, session)
