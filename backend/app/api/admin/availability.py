from __future__ import annotations

from datetime import date, datetime, time
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.admin.dependencies import get_admin_tenant_context
from app.db.session import get_db_session
from app.models.tenant import AvailabilityException, AvailabilityRule, Location, Organization, Practitioner, PractitionerService, Room
from app.services.availability import AvailableSlot, InternalSchedulingProvider, SchedulingProvider
from app.services.errors import BusinessRuleViolation, ConflictError, DomainValidationError, ResourceNotFound
from app.tenancy.context import TenantContext

router = APIRouter(tags=["admin-availability"])


class CreateAvailabilityRuleRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    organization_id: UUID
    practitioner_id: UUID
    practitioner_service_id: UUID | None = None
    location_id: UUID | None = None
    room_id: UUID | None = None
    modality: Literal["in_person", "virtual", "both"]
    weekday: int = Field(ge=1, le=7)
    start_time: time
    end_time: time
    valid_from: date
    valid_to: date | None = None
    buffer_minutes: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_range_fields(self) -> "CreateAvailabilityRuleRequest":
        if self.start_time >= self.end_time:
            raise ValueError("start_time must be before end_time")
        if self.valid_to is not None and self.valid_to < self.valid_from:
            raise ValueError("valid_to must not be before valid_from")
        return self


class CreateAvailabilityExceptionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    practitioner_id: UUID
    location_id: UUID | None = None
    room_id: UUID | None = None
    starts_at: datetime
    ends_at: datetime
    exception_type: Literal["blocked", "unavailable", "vacation", "medical_leave", "personal", "meeting", "lunch", "training", "maintenance", "temporary_closure", "administrative", "other"]
    reason: str | None = None

    @model_validator(mode="after")
    def validate_range_fields(self) -> "CreateAvailabilityExceptionRequest":
        if self.starts_at >= self.ends_at:
            raise ValueError("starts_at must be before ends_at")
        return self


AVAILABILITY_EXCEPTION_TYPES = {
    "vacation": "Vacaciones",
    "medical_leave": "Incapacidad",
    "personal": "Espacio personal",
    "meeting": "Reunión",
    "lunch": "Almuerzo",
    "training": "Capacitación",
    "maintenance": "Mantenimiento",
    "temporary_closure": "Cierre temporal",
    "administrative": "Bloqueo administrativo",
    "other": "Otro",
    # Legacy phase 4 aliases kept for backward compatibility.
    "blocked": "Bloqueado",
    "unavailable": "No disponible",
}
MVP_AVAILABILITY_EXCEPTION_TYPES = set(AVAILABILITY_EXCEPTION_TYPES) - {"blocked", "unavailable"}


class PatchAvailabilityExceptionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    starts_at: datetime | None = None
    ends_at: datetime | None = None
    exception_type: Literal["vacation", "medical_leave", "personal", "meeting", "lunch", "training", "maintenance", "temporary_closure", "administrative", "other"] | None = None
    reason: str | None = None
    status: Literal["active", "inactive"] | None = None


class DisableAvailabilityExceptionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

def get_scheduling_provider() -> SchedulingProvider:
    return InternalSchedulingProvider()


def _validate_location_room(session: Session, location_id: UUID | None, room_id: UUID | None) -> None:
    if location_id is not None and session.get(Location, location_id) is None:
        raise ResourceNotFound("Location not found.")
    if room_id is None:
        return
    if location_id is None:
        raise DomainValidationError("room_id requires location_id.")
    room = session.get(Room, room_id)
    if room is None:
        raise ResourceNotFound("Room not found.")
    if room.location_id != location_id:
        raise BusinessRuleViolation("Room does not belong to the provided location.")


def serialize_availability_rule(rule: AvailabilityRule) -> dict[str, object]:
    return {
        "id": str(rule.id),
        "organization_id": str(rule.organization_id),
        "practitioner_id": str(rule.practitioner_id),
        "practitioner_service_id": str(rule.practitioner_service_id) if rule.practitioner_service_id is not None else None,
        "location_id": str(rule.location_id) if rule.location_id is not None else None,
        "room_id": str(rule.room_id) if rule.room_id is not None else None,
        "modality": rule.modality,
        "weekday": rule.weekday,
        "start_time": rule.start_time.isoformat(),
        "end_time": rule.end_time.isoformat(),
        "valid_from": rule.valid_from.isoformat(),
        "valid_to": rule.valid_to.isoformat() if rule.valid_to is not None else None,
        "buffer_minutes": rule.buffer_minutes,
        "status": rule.status,
    }


def serialize_availability_exception(exception: AvailabilityException, session: Session | None = None) -> dict[str, object]:
    practitioner = session.get(Practitioner, exception.practitioner_id) if session is not None else None
    room = session.get(Room, exception.room_id) if session is not None and exception.room_id is not None else None
    location = session.get(Location, exception.location_id) if session is not None and exception.location_id is not None else None
    if location is None and session is not None and room is not None:
        location = session.get(Location, room.location_id)
    organization = session.get(Organization, location.organization_id) if session is not None and location is not None else None
    return {
        "id": str(exception.id),
        "practitioner_id": str(exception.practitioner_id),
        "practitioner_name": practitioner.full_name if practitioner is not None else None,
        "practitioner_status": practitioner.status if practitioner is not None else None,
        "location_id": str(exception.location_id) if exception.location_id is not None else None,
        "location_name": location.name if location is not None else None,
        "location_status": location.status if location is not None else None,
        "organization_id": str(organization.id) if organization is not None else None,
        "organization_name": organization.name if organization is not None else None,
        "organization_status": organization.status if organization is not None else None,
        "room_id": str(exception.room_id) if exception.room_id is not None else None,
        "room_name": room.name if room is not None else None,
        "room_status": room.status if room is not None else None,
        "starts_at": exception.starts_at.isoformat(),
        "ends_at": exception.ends_at.isoformat(),
        "exception_type": exception.exception_type,
        "exception_type_label": AVAILABILITY_EXCEPTION_TYPES.get(exception.exception_type, exception.exception_type),
        "reason": exception.reason,
        "status": exception.status,
    }



def _validate_exception_dates(starts_at: datetime, ends_at: datetime) -> None:
    if starts_at >= ends_at:
        raise DomainValidationError("starts_at must be before ends_at.")


def _validate_exception_active_parents(session: Session, practitioner_id: UUID, location_id: UUID | None, room_id: UUID | None) -> None:
    practitioner = session.get(Practitioner, practitioner_id)
    if practitioner is None:
        raise ResourceNotFound("Practitioner not found.")
    if practitioner.status != "active":
        raise BusinessRuleViolation("Availability exceptions require an active practitioner.")
    location = session.get(Location, location_id) if location_id is not None else None
    if location_id is not None and location is None:
        raise ResourceNotFound("Location not found.")
    if location is not None:
        if location.status != "active":
            raise BusinessRuleViolation("Availability exceptions require an active location.")
        organization = session.get(Organization, location.organization_id)
        if organization is None:
            raise ResourceNotFound("Organization not found.")
        if organization.status != "active":
            raise BusinessRuleViolation("Availability exceptions require an active organization.")
    room = session.get(Room, room_id) if room_id is not None else None
    if room_id is not None and room is None:
        raise ResourceNotFound("Room not found.")
    if room is not None:
        if room.status != "active":
            raise BusinessRuleViolation("Availability exceptions require an active room.")
        if location_id is not None and room.location_id != location_id:
            raise BusinessRuleViolation("Room does not belong to the provided location.")
        if location_id is None:
            room_location = session.get(Location, room.location_id)
            if room_location is None:
                raise ResourceNotFound("Location not found.")
            if room_location.status != "active":
                raise BusinessRuleViolation("Availability exceptions require an active location.")
            organization = session.get(Organization, room_location.organization_id)
            if organization is None:
                raise ResourceNotFound("Organization not found.")
            if organization.status != "active":
                raise BusinessRuleViolation("Availability exceptions require an active organization.")


def _validate_no_exact_active_exception_duplicate(session: Session, practitioner_id: UUID, location_id: UUID | None, room_id: UUID | None, exception_type: str, starts_at: datetime, ends_at: datetime, exclude_id: UUID | None = None) -> None:
    stmt = select(AvailabilityException).where(AvailabilityException.status == "active", AvailabilityException.practitioner_id == practitioner_id, AvailabilityException.exception_type == exception_type, AvailabilityException.starts_at == starts_at, AvailabilityException.ends_at == ends_at)
    stmt = stmt.where(AvailabilityException.location_id.is_(None) if location_id is None else AvailabilityException.location_id == location_id)
    stmt = stmt.where(AvailabilityException.room_id.is_(None) if room_id is None else AvailabilityException.room_id == room_id)
    if exclude_id is not None:
        stmt = stmt.where(AvailabilityException.id != exclude_id)
    if session.scalar(stmt) is not None:
        raise ConflictError("Active availability exception already exists for the same practitioner, context, type and range.")

def serialize_slot(slot: AvailableSlot) -> dict[str, object]:
    return {
        "starts_at": slot.starts_at.isoformat(),
        "ends_at": slot.ends_at.isoformat(),
        "practitioner_id": str(slot.practitioner_id),
        "location_id": str(slot.location_id) if slot.location_id is not None else None,
        "room_id": str(slot.room_id) if slot.room_id is not None else None,
        "modality": slot.modality,
        "source": slot.source,
    }


@router.post("/availability-rules")
def create_availability_rule(
    payload: CreateAvailabilityRuleRequest,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, dict[str, object]]:
    _ = tenant_context
    if session.get(Organization, payload.organization_id) is None:
        raise ResourceNotFound("Organization not found.")
    if session.get(Practitioner, payload.practitioner_id) is None:
        raise ResourceNotFound("Practitioner not found.")
    if payload.practitioner_service_id is not None and session.get(PractitionerService, payload.practitioner_service_id) is None:
        raise ResourceNotFound("Practitioner service not found.")
    if payload.modality == "virtual" and (payload.location_id is not None or payload.room_id is not None):
        raise DomainValidationError("Virtual availability rules must not include location_id or room_id.")
    _validate_location_room(session, payload.location_id, payload.room_id)

    rule = AvailabilityRule(**payload.model_dump())
    try:
        session.add(rule)
        session.flush()
        session.refresh(rule)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return {"data": serialize_availability_rule(rule)}


@router.post("/availability-exceptions")
def create_availability_exception(
    payload: CreateAvailabilityExceptionRequest,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, dict[str, object]]:
    _ = tenant_context
    _validate_exception_active_parents(session, payload.practitioner_id, payload.location_id, payload.room_id)
    _validate_no_exact_active_exception_duplicate(session, payload.practitioner_id, payload.location_id, payload.room_id, payload.exception_type, payload.starts_at, payload.ends_at)

    exception = AvailabilityException(**payload.model_dump(), status="active")
    try:
        session.add(exception)
        session.flush()
        session.refresh(exception)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return {"data": serialize_availability_exception(exception, session)}


@router.get("/availability-exceptions")
def list_availability_exceptions(practitioner_id: UUID | None = None, location_id: UUID | None = None, room_id: UUID | None = None, exception_type: str | None = None, status: str | None = None, include_inactive: bool = False, starts_from: datetime | None = None, starts_to: datetime | None = None, tenant_context: TenantContext = Depends(get_admin_tenant_context), session: Session = Depends(get_db_session)) -> dict[str, list[dict[str, object]]]:
    _ = tenant_context
    stmt = select(AvailabilityException)
    if practitioner_id is not None: stmt = stmt.where(AvailabilityException.practitioner_id == practitioner_id)
    if location_id is not None: stmt = stmt.where(AvailabilityException.location_id == location_id)
    if room_id is not None: stmt = stmt.where(AvailabilityException.room_id == room_id)
    if exception_type is not None: stmt = stmt.where(AvailabilityException.exception_type == exception_type)
    if status is not None: stmt = stmt.where(AvailabilityException.status == status)
    elif not include_inactive: stmt = stmt.where(AvailabilityException.status == "active")
    if starts_from is not None: stmt = stmt.where(AvailabilityException.starts_at >= starts_from)
    if starts_to is not None: stmt = stmt.where(AvailabilityException.starts_at <= starts_to)
    rows = session.scalars(stmt.order_by(AvailabilityException.starts_at, AvailabilityException.id)).all()
    return {"data": [serialize_availability_exception(row, session) for row in rows]}


@router.get("/availability-exceptions/{exception_id}")
def get_availability_exception(exception_id: UUID, tenant_context: TenantContext = Depends(get_admin_tenant_context), session: Session = Depends(get_db_session)) -> dict[str, dict[str, object]]:
    _ = tenant_context
    exception = session.get(AvailabilityException, exception_id)
    if exception is None: raise ResourceNotFound("Availability exception not found.")
    return {"data": serialize_availability_exception(exception, session)}


@router.patch("/availability-exceptions/{exception_id}")
def patch_availability_exception(exception_id: UUID, payload: PatchAvailabilityExceptionRequest, tenant_context: TenantContext = Depends(get_admin_tenant_context), session: Session = Depends(get_db_session)) -> dict[str, dict[str, object]]:
    _ = tenant_context
    exception = session.get(AvailabilityException, exception_id)
    if exception is None: raise ResourceNotFound("Availability exception not found.")
    data = payload.model_dump(exclude_unset=True)
    starts_at = data.get("starts_at", exception.starts_at); ends_at = data.get("ends_at", exception.ends_at); exception_type = data.get("exception_type", exception.exception_type); status = data.get("status", exception.status)
    _validate_exception_dates(starts_at, ends_at)
    if status == "active":
        _validate_exception_active_parents(session, exception.practitioner_id, exception.location_id, exception.room_id)
        _validate_no_exact_active_exception_duplicate(session, exception.practitioner_id, exception.location_id, exception.room_id, exception_type, starts_at, ends_at, exclude_id=exception_id)
    for field, value in data.items(): setattr(exception, field, value)
    try:
        session.flush(); data_out = serialize_availability_exception(exception, session); session.commit()
    except Exception:
        session.rollback(); raise
    return {"data": data_out}


@router.post("/availability-exceptions/{exception_id}/disable")
def disable_availability_exception(exception_id: UUID, payload: DisableAvailabilityExceptionRequest, tenant_context: TenantContext = Depends(get_admin_tenant_context), session: Session = Depends(get_db_session)) -> dict[str, dict[str, object]]:
    _ = (tenant_context, payload)
    exception = session.get(AvailabilityException, exception_id)
    if exception is None: raise ResourceNotFound("Availability exception not found.")
    exception.status = "inactive"
    try:
        session.flush(); data = serialize_availability_exception(exception, session); session.commit()
    except Exception:
        session.rollback(); raise
    return {"data": data}


@router.get("/availability/slots")
def list_availability_slots(
    practitioner_service_id: UUID,
    modality: str,
    date_from: date,
    date_to: date,
    practitioner_id: UUID | None = None,
    payer_plan_id: UUID | None = Query(default=None),
    location_id: UUID | None = None,
    room_id: UUID | None = None,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
    scheduling_provider: SchedulingProvider = Depends(get_scheduling_provider),
) -> dict[str, list[dict[str, object]]]:
    # payer_plan_id is intentionally accepted for API-contract compatibility; pricing
    # remains out of scope for availability slot lookup in this PR.
    _ = payer_plan_id
    slots = scheduling_provider.list_available_slots(
        session,
        tenant_context,
        practitioner_service_id=practitioner_service_id,
        practitioner_id=practitioner_id,
        modality=modality,
        start_date=date_from,
        end_date=date_to,
        location_id=location_id,
        room_id=room_id,
    )
    return {"data": [serialize_slot(slot) for slot in slots]}
