from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.api.admin.dependencies import get_admin_tenant_context
from app.db.session import get_db_session
from app.models.tenant import Booking
from app.services.booking import BookingService
from app.services.availability import InternalSchedulingProvider, SchedulingProvider
from app.tenancy.context import TenantContext

router = APIRouter(prefix="/bookings", tags=["admin-bookings"])


class AdminBookingPatientRequest(BaseModel):
    id: UUID | None = None
    full_name: str | None = None
    phone: str | None = None
    email: str | None = None


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
        "service_name_snapshot": booking.service_name_snapshot,
        "payer_plan_name_snapshot": booking.payer_plan_name_snapshot,
        "price_snapshot": _serialize_amount(booking.price_snapshot),
        "currency_snapshot": booking.currency_snapshot,
        "total_amount": _serialize_amount(booking.total_amount),
    }


def _serialize_amount(value: Decimal) -> int | float:
    if value == value.to_integral_value():
        return int(value)
    return float(value)


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
