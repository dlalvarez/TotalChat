from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.admin.dependencies import get_admin_tenant_context
from app.db.session import get_db_session
from app.models.tenant import Booking
from app.services.booking import BookingService
from app.services.errors import ResourceNotFound
from app.services.availability import InternalSchedulingProvider, SchedulingProvider
from app.tenancy.context import TenantContext

router = APIRouter(prefix="/bookings", tags=["admin-bookings"])


class AdminBookingPatientRequest(BaseModel):
    id: UUID | None = None
    full_name: str | None = None
    phone: str | None = None
    email: str | None = None


class ConfirmAdminBookingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CancelAdminBookingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str
    release_slot: bool = True


class CreateAdminBookingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patient: AdminBookingPatientRequest
    practitioner_service_id: UUID
    payer_plan_id: UUID
    modality: str
    starts_at: datetime
    location_id: UUID | None = None
    room_id: UUID | None = None
    created_channel: str | None = "admin"


def get_booking_scheduling_provider() -> SchedulingProvider:
    return InternalSchedulingProvider()


def serialize_booking(booking: Booking) -> dict[str, object]:
    return {
        "id": str(booking.id),
        "patient_id": str(booking.patient_id),
        "practitioner_service_id": str(booking.practitioner_service_id),
        "payer_plan_id": str(booking.payer_plan_id) if booking.payer_plan_id is not None else None,
        "location_id": str(booking.location_id) if booking.location_id is not None else None,
        "room_id": str(booking.room_id) if booking.room_id is not None else None,
        "status": booking.status,
        "payment_status": booking.payment_status,
        "starts_at": booking.starts_at.isoformat(),
        "ends_at": booking.ends_at.isoformat(),
        "modality": booking.modality,
        "service_name_snapshot": booking.service_name_snapshot,
        "practitioner_name_snapshot": booking.practitioner_name_snapshot,
        "payer_plan_name_snapshot": booking.payer_plan_name_snapshot,
        "price_snapshot": _serialize_amount(booking.price_snapshot),
        "currency_snapshot": booking.currency_snapshot,
        "total_amount": _serialize_amount(booking.total_amount),
        "admin_cancellation_reason": booking.admin_cancellation_reason,
    }


def _serialize_amount(value: Decimal) -> int | float:
    if value == value.to_integral_value():
        return int(value)
    return float(value)


@router.post("/{booking_id}/confirm")
def confirm_admin_booking(
    booking_id: UUID,
    payload: ConfirmAdminBookingRequest = Body(default_factory=ConfirmAdminBookingRequest),
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, dict[str, object]]:
    _ = payload
    try:
        booking = BookingService(session, tenant_context).confirm_booking(booking_id)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return {"data": serialize_booking(booking)}


@router.post("/{booking_id}/cancel")
def cancel_admin_booking(
    booking_id: UUID,
    payload: CancelAdminBookingRequest,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, dict[str, object]]:
    try:
        booking = BookingService(session, tenant_context).cancel_booking_by_admin(booking_id, reason=payload.reason, release_slot=payload.release_slot)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return {"data": serialize_booking(booking)}


@router.get("/{booking_id}")
def get_admin_booking(
    booking_id: UUID,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, dict[str, object]]:
    booking = session.get(Booking, booking_id)
    if booking is None:
        raise ResourceNotFound("Booking not found.")

    return {"data": serialize_booking(booking)}


@router.get("")
def list_admin_bookings(
    status: str | None = None,
    practitioner_id: UUID | None = None,
    patient_id: UUID | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, object]:
    stmt = select(Booking)
    if status is not None:
        stmt = stmt.where(Booking.status == status)
    if practitioner_id is not None:
        stmt = stmt.where(Booking.practitioner_id == practitioner_id)
    if patient_id is not None:
        stmt = stmt.where(Booking.patient_id == patient_id)
    if date_from is not None:
        stmt = stmt.where(Booking.starts_at >= datetime.combine(date_from, time.min))
    if date_to is not None:
        stmt = stmt.where(Booking.starts_at <= datetime.combine(date_to, time.max))

    stmt = stmt.order_by(Booking.starts_at, Booking.id).limit(limit).offset(offset)
    bookings = session.scalars(stmt).all()
    return {"data": [serialize_booking(booking) for booking in bookings], "meta": {"limit": limit, "offset": offset}}


@router.post("")
def create_admin_booking(
    payload: CreateAdminBookingRequest,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
    scheduling_provider: SchedulingProvider = Depends(get_booking_scheduling_provider),
) -> dict[str, dict[str, object]]:
    patient_id = payload.patient.id
    patient_data = None
    if patient_id is None:
        patient_data = {
            "full_name": payload.patient.full_name,
            "phone": payload.patient.phone,
            "email": payload.patient.email,
            "created_from_channel": payload.created_channel,
        }

    try:
        booking = BookingService(session, tenant_context, scheduling_provider=scheduling_provider).create_tentative_booking(
            practitioner_service_id=payload.practitioner_service_id,
            payer_plan_id=payload.payer_plan_id,
            starts_at=payload.starts_at,
            modality=payload.modality,
            patient_id=patient_id,
            patient_data=patient_data,
            location_id=payload.location_id,
            room_id=payload.room_id,
            created_channel=payload.created_channel,
        )
        session.commit()
    except Exception:
        session.rollback()
        raise

    return {"data": serialize_booking(booking)}
