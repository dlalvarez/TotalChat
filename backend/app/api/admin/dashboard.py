from __future__ import annotations

from datetime import datetime, time, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.admin.dependencies import get_admin_tenant_context
from app.db.session import get_db_session
from app.models.tenant import Booking, Location, Patient, PaymentAttempt, Practitioner, PractitionerService
from app.tenancy.context import TenantContext

router = APIRouter(prefix="/dashboard", tags=["admin-dashboard"])


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _day_bounds(value: datetime) -> tuple[datetime, datetime]:
    current_date = value.date()
    return (
        datetime.combine(current_date, time.min, tzinfo=timezone.utc),
        datetime.combine(current_date, time.max, tzinfo=timezone.utc),
    )


def _count(session: Session, stmt) -> int:
    return int(session.scalar(stmt) or 0)


def _amount(value: Decimal | None) -> float | None:
    return float(value) if value is not None else None


def _appointment_item(booking: Booking, *, patient: Patient | None = None, practitioner: Practitioner | None = None, service: PractitionerService | None = None, location: Location | None = None) -> dict[str, object]:
    return {
        "id": str(booking.id),
        "starts_at": booking.starts_at.isoformat(),
        "patient_name": patient.full_name if patient else "Paciente sin nombre",
        "practitioner_name": practitioner.full_name if practitioner else booking.practitioner_name_snapshot,
        "service_name": service.name if service else booking.service_name_snapshot,
        "location_name": location.name if location else booking.location_name_snapshot,
        "status": booking.status,
        "payment_status": booking.payment_status,
    }


def _payment_review_item(attempt: PaymentAttempt) -> dict[str, object]:
    booking = attempt.booking
    return {
        "id": str(attempt.id),
        "booking_id": str(attempt.booking_id),
        "patient_name": booking.patient.full_name if getattr(booking, "patient", None) else "Paciente sin nombre",
        "practitioner_name": booking.practitioner.full_name if getattr(booking, "practitioner", None) else booking.practitioner_name_snapshot,
        "service_name": booking.practitioner_service.name if getattr(booking, "practitioner_service", None) else booking.service_name_snapshot,
        "amount": _amount(attempt.amount),
        "currency": attempt.currency,
        "evidence_received_at": attempt.evidence_received_at.isoformat() if attempt.evidence_received_at else None,
    }


def _virtual_alert_item(booking: Booking) -> dict[str, object]:
    return {
        "id": str(booking.id),
        "starts_at": booking.starts_at.isoformat(),
        "patient_name": booking.patient.full_name if getattr(booking, "patient", None) else "Paciente sin nombre",
        "practitioner_name": booking.practitioner.full_name if getattr(booking, "practitioner", None) else booking.practitioner_name_snapshot,
        "service_name": booking.practitioner_service.name if getattr(booking, "practitioner_service", None) else booking.service_name_snapshot,
        "location_name": booking.location.name if getattr(booking, "location", None) else booking.location_name_snapshot,
    }


@router.get("/summary")
def get_dashboard_summary(
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
):
    _ = tenant_context
    now = _now()
    today_start, today_end = _day_bounds(now)

    appointments_today_stmt = select(func.count()).select_from(Booking).where(Booking.starts_at >= today_start, Booking.starts_at <= today_end)
    upcoming_stmt = select(func.count()).select_from(Booking).where(Booking.status == "scheduled", Booking.starts_at > now)
    pending_payment_stmt = select(func.count()).select_from(Booking).where(Booking.payment_status == "pending")
    pending_reviews_stmt = select(func.count()).select_from(PaymentAttempt).where(
        PaymentAttempt.method == "transfer",
        PaymentAttempt.status == "evidence_received",
        PaymentAttempt.evidence_received_at.is_not(None),
    )
    virtual_without_link_stmt = select(func.count()).select_from(Booking).where(
        Booking.status == "scheduled",
        Booking.modality == "virtual",
        Booking.virtual_meeting_url.is_(None),
    )
    active_services_stmt = select(func.count()).select_from(PractitionerService).where(PractitionerService.status == "active")
    active_practitioners_stmt = select(func.count()).select_from(Practitioner).where(Practitioner.status == "active")

    today_rows = session.execute(
        select(Booking, Patient, Practitioner, PractitionerService, Location)
        .join(Patient, Booking.patient_id == Patient.id)
        .join(Practitioner, Booking.practitioner_id == Practitioner.id)
        .join(PractitionerService, Booking.practitioner_service_id == PractitionerService.id)
        .outerjoin(Location, Booking.location_id == Location.id)
        .where(Booking.starts_at >= max(now, today_start), Booking.starts_at <= today_end)
        .order_by(Booking.starts_at.asc())
        .limit(10)
    ).all()

    review_rows = session.scalars(
        select(PaymentAttempt)
        .options(
            selectinload(PaymentAttempt.booking).selectinload(Booking.patient),
            selectinload(PaymentAttempt.booking).selectinload(Booking.practitioner),
            selectinload(PaymentAttempt.booking).selectinload(Booking.practitioner_service),
        )
        .join(Booking, PaymentAttempt.booking_id == Booking.id)
        .where(PaymentAttempt.method == "transfer", PaymentAttempt.status == "evidence_received", PaymentAttempt.evidence_received_at.is_not(None))
        .order_by(PaymentAttempt.evidence_received_at.asc(), PaymentAttempt.id.asc())
        .limit(10)
    ).unique().all()

    virtual_rows = session.scalars(
        select(Booking)
        .options(selectinload(Booking.patient), selectinload(Booking.practitioner), selectinload(Booking.practitioner_service), selectinload(Booking.location))
        .where(Booking.status == "scheduled", Booking.modality == "virtual", Booking.virtual_meeting_url.is_(None))
        .order_by(Booking.starts_at.asc())
        .limit(10)
    ).unique().all()

    return {
        "data": {
            "metrics": {
                "appointments_today": _count(session, appointments_today_stmt),
                "upcoming_appointments": _count(session, upcoming_stmt),
                "appointments_pending_payment": _count(session, pending_payment_stmt),
                "payment_reviews_pending": _count(session, pending_reviews_stmt),
                "virtual_appointments_without_link": _count(session, virtual_without_link_stmt),
                "active_services": _count(session, active_services_stmt),
                "active_practitioners": _count(session, active_practitioners_stmt),
            },
            "today_appointments": [_appointment_item(booking, patient=patient, practitioner=practitioner, service=service, location=location) for booking, patient, practitioner, service, location in today_rows],
            "pending_payment_reviews": [_payment_review_item(row) for row in review_rows],
            "virtual_link_alerts": [_virtual_alert_item(row) for row in virtual_rows],
        }
    }
