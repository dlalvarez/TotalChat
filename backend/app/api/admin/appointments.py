from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, model_validator
from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from app.api.admin.dependencies import get_admin_tenant_context
from app.db.session import get_db_session
from app.models.tenant import AvailabilityException, Booking, Location, Organization, OrganizationPractitioner, Patient, Practitioner, PractitionerService, Room
from app.services.errors import BusinessRuleViolation, ConflictError, DomainValidationError, ResourceNotFound
from app.tenancy.context import TenantContext

router = APIRouter(prefix="/appointments", tags=["admin-appointments"])
APPOINTMENT_STATUSES = {"scheduled", "cancelled", "completed", "no_show"}
APPOINTMENT_STATUS_LABELS = {"scheduled": "Programada", "cancelled": "Cancelada", "completed": "Atendida", "no_show": "No asistió"}

class CreateAppointmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    organization_id: UUID
    location_id: UUID
    room_id: UUID | None = None
    practitioner_id: UUID
    practitioner_service_id: UUID
    patient_id: UUID
    starts_at: datetime
    ends_at: datetime
    notes: str | None = None
    @model_validator(mode="after")
    def validate_range(self) -> "CreateAppointmentRequest":
        if self.starts_at >= self.ends_at:
            raise ValueError("starts_at must be before ends_at.")
        return self

class PatchAppointmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    notes: str | None = None

class EmptyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

def _overlap(model, starts_at: datetime, ends_at: datetime):
    return (model.starts_at < ends_at, starts_at < model.ends_at)

def _validate_payload(session: Session, p: CreateAppointmentRequest, exclude_id: UUID | None = None) -> tuple[Organization, Location, Room | None, Practitioner, PractitionerService, Patient]:
    org = session.get(Organization, p.organization_id)
    if org is None: raise ResourceNotFound("Organization not found.")
    if org.status != "active": raise BusinessRuleViolation("Appointment requires an active organization.")
    loc = session.get(Location, p.location_id)
    if loc is None: raise ResourceNotFound("Location not found.")
    if loc.status != "active": raise BusinessRuleViolation("Appointment requires an active location.")
    if loc.organization_id != org.id: raise BusinessRuleViolation("Location does not belong to the organization.")
    room = session.get(Room, p.room_id) if p.room_id is not None else None
    if p.room_id is not None and room is None: raise ResourceNotFound("Room not found.")
    if room is not None:
        if room.status != "active": raise BusinessRuleViolation("Appointment requires an active room.")
        if room.location_id != loc.id: raise BusinessRuleViolation("Room does not belong to the location.")
    practitioner = session.get(Practitioner, p.practitioner_id)
    if practitioner is None: raise ResourceNotFound("Practitioner not found.")
    if practitioner.status != "active": raise BusinessRuleViolation("Appointment requires an active practitioner.")
    rel = session.scalar(select(OrganizationPractitioner).where(OrganizationPractitioner.organization_id == org.id, OrganizationPractitioner.practitioner_id == practitioner.id))
    if rel is None or rel.status != "active": raise BusinessRuleViolation("Appointment requires an active organization-practitioner relationship.")
    service = session.get(PractitionerService, p.practitioner_service_id)
    if service is None: raise ResourceNotFound("Practitioner service not found.")
    if service.status != "active": raise BusinessRuleViolation("Appointment requires an active practitioner service.")
    if service.practitioner_id != practitioner.id: raise BusinessRuleViolation("Practitioner service does not belong to the selected practitioner.")
    if service.organization_id != org.id: raise BusinessRuleViolation("Practitioner service does not belong to the selected organization.")
    patient = session.get(Patient, p.patient_id)
    if patient is None: raise ResourceNotFound("Patient not found.")
    if p.starts_at >= p.ends_at: raise DomainValidationError("starts_at must be before ends_at.")

    stmt = select(AvailabilityException).where(AvailabilityException.status == "active", AvailabilityException.practitioner_id == practitioner.id, AvailabilityException.starts_at < p.ends_at, p.starts_at < AvailabilityException.ends_at)
    stmt = stmt.where(or_(AvailabilityException.location_id.is_(None), AvailabilityException.location_id == loc.id))
    if room is not None:
        stmt = stmt.where(or_(AvailabilityException.room_id.is_(None), AvailabilityException.room_id == room.id))
    else:
        stmt = stmt.where(AvailabilityException.room_id.is_(None))
    if session.scalar(stmt) is not None: raise ConflictError("Appointment overlaps an active availability exception.")

    bstmt = select(Booking).where(Booking.status == "scheduled", Booking.practitioner_id == practitioner.id, Booking.starts_at < p.ends_at, p.starts_at < Booking.ends_at)
    if exclude_id is not None: bstmt = bstmt.where(Booking.id != exclude_id)
    if session.scalar(bstmt) is not None: raise ConflictError("Practitioner already has a scheduled appointment in this time range.")
    if room is not None:
        rstmt = select(Booking).where(Booking.status == "scheduled", Booking.room_id == room.id, Booking.starts_at < p.ends_at, p.starts_at < Booking.ends_at)
        if exclude_id is not None: rstmt = rstmt.where(Booking.id != exclude_id)
        if session.scalar(rstmt) is not None: raise ConflictError("Room already has a scheduled appointment in this time range.")
    return org, loc, room, practitioner, service, patient

def serialize_appointment(a: Booking, session: Session) -> dict[str, object]:
    org = session.get(Organization, a.organization_id)
    loc = session.get(Location, a.location_id) if a.location_id else None
    room = session.get(Room, a.room_id) if a.room_id else None
    practitioner = session.get(Practitioner, a.practitioner_id)
    service = session.get(PractitionerService, a.practitioner_service_id)
    patient = session.get(Patient, a.patient_id)
    return {"id": str(a.id), "organization_id": str(a.organization_id), "organization_name": org.name if org else None, "location_id": str(a.location_id) if a.location_id else None, "location_name": loc.name if loc else a.location_name_snapshot, "room_id": str(a.room_id) if a.room_id else None, "room_name": room.name if room else a.room_snapshot, "practitioner_id": str(a.practitioner_id), "practitioner_name": practitioner.full_name if practitioner else a.practitioner_name_snapshot, "practitioner_service_id": str(a.practitioner_service_id), "practitioner_service_name": service.name if service else a.service_name_snapshot, "patient_id": str(a.patient_id), "patient_name": patient.full_name if patient else None, "starts_at": a.starts_at.isoformat(), "ends_at": a.ends_at.isoformat(), "status": a.status, "status_label": APPOINTMENT_STATUS_LABELS.get(a.status, a.status), "notes": getattr(a, "notes", None), "created_at": a.created_at.isoformat() if a.created_at else None, "updated_at": a.updated_at.isoformat() if a.updated_at else None}

@router.get("")
def list_appointments(organization_id: UUID | None = None, location_id: UUID | None = None, room_id: UUID | None = None, practitioner_id: UUID | None = None, practitioner_service_id: UUID | None = None, patient_id: UUID | None = None, status: str | None = None, date: date | None = None, date_from: date | None = None, date_to: date | None = None, tenant_context: TenantContext = Depends(get_admin_tenant_context), session: Session = Depends(get_db_session)):
    _ = tenant_context
    stmt = select(Booking).where(Booking.status.in_(APPOINTMENT_STATUSES))
    for field, value in [(Booking.organization_id, organization_id),(Booking.location_id, location_id),(Booking.room_id, room_id),(Booking.practitioner_id, practitioner_id),(Booking.practitioner_service_id, practitioner_service_id),(Booking.patient_id, patient_id)]:
        if value is not None: stmt = stmt.where(field == value)
    if status is not None: stmt = stmt.where(Booking.status == status)
    if date is not None:
        stmt = stmt.where(Booking.starts_at >= datetime.combine(date, time.min), Booking.starts_at <= datetime.combine(date, time.max))
    if date_from is not None: stmt = stmt.where(Booking.starts_at >= datetime.combine(date_from, time.min))
    if date_to is not None: stmt = stmt.where(Booking.starts_at <= datetime.combine(date_to, time.max))
    rows = session.scalars(stmt.order_by(Booking.starts_at, Booking.id)).all()
    return {"data": [serialize_appointment(r, session) for r in rows]}

@router.get("/{appointment_id}")
def get_appointment(appointment_id: UUID, tenant_context: TenantContext = Depends(get_admin_tenant_context), session: Session = Depends(get_db_session)):
    _ = tenant_context; a = session.get(Booking, appointment_id)
    if a is None or a.status not in APPOINTMENT_STATUSES: raise ResourceNotFound("Appointment not found.")
    return {"data": serialize_appointment(a, session)}

@router.post("")
def create_appointment(payload: CreateAppointmentRequest, tenant_context: TenantContext = Depends(get_admin_tenant_context), session: Session = Depends(get_db_session)):
    _ = tenant_context
    org, loc, room, practitioner, service, patient = _validate_payload(session, payload)
    a = Booking(organization_id=org.id, patient_id=patient.id, practitioner_id=practitioner.id, practitioner_service_id=service.id, location_id=loc.id, room_id=room.id if room else None, modality="in_person", starts_at=payload.starts_at, ends_at=payload.ends_at, status="scheduled", payment_status="pending", service_name_snapshot=service.name, duration_minutes_snapshot=max(1, int((payload.ends_at - payload.starts_at).total_seconds() // 60)), practitioner_name_snapshot=practitioner.full_name, modality_snapshot="in_person", location_name_snapshot=loc.name, room_snapshot=room.name if room else None, price_snapshot=Decimal("0.00"), currency_snapshot="COP", total_amount=Decimal("0.00"), created_channel="admin", pending_patient_data=False, notes=payload.notes)
    try:
        session.add(a); session.flush(); data = serialize_appointment(a, session); session.commit()
    except Exception:
        session.rollback(); raise
    return {"data": data}

@router.patch("/{appointment_id}")
def patch_appointment(appointment_id: UUID, payload: PatchAppointmentRequest, tenant_context: TenantContext = Depends(get_admin_tenant_context), session: Session = Depends(get_db_session)):
    _ = tenant_context; a = session.get(Booking, appointment_id)
    if a is None or a.status not in APPOINTMENT_STATUSES: raise ResourceNotFound("Appointment not found.")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items(): setattr(a, k, v)
    try:
        session.flush(); out = serialize_appointment(a, session); session.commit()
    except Exception:
        session.rollback(); raise
    return {"data": out}

def _set_status(appointment_id: UUID, status: str, session: Session):
    a = session.get(Booking, appointment_id)
    if a is None or a.status not in APPOINTMENT_STATUSES: raise ResourceNotFound("Appointment not found.")
    a.status = status
    try:
        session.flush(); out = serialize_appointment(a, session); session.commit()
    except Exception:
        session.rollback(); raise
    return {"data": out}

@router.post("/{appointment_id}/cancel")
def cancel_appointment(appointment_id: UUID, payload: EmptyRequest, tenant_context: TenantContext = Depends(get_admin_tenant_context), session: Session = Depends(get_db_session)):
    _ = (tenant_context, payload); return _set_status(appointment_id, "cancelled", session)
@router.post("/{appointment_id}/complete")
def complete_appointment(appointment_id: UUID, payload: EmptyRequest, tenant_context: TenantContext = Depends(get_admin_tenant_context), session: Session = Depends(get_db_session)):
    _ = (tenant_context, payload); return _set_status(appointment_id, "completed", session)
@router.post("/{appointment_id}/no-show")
def no_show_appointment(appointment_id: UUID, payload: EmptyRequest, tenant_context: TenantContext = Depends(get_admin_tenant_context), session: Session = Depends(get_db_session)):
    _ = (tenant_context, payload); return _set_status(appointment_id, "no_show", session)
