from __future__ import annotations

from datetime import date, datetime, time
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy.orm import Session

from app.api.admin.dependencies import get_admin_tenant_context
from app.db.session import get_db_session
from app.models.tenant import AvailabilityException, AvailabilityRule, Location, Organization, Practitioner, PractitionerService, Room
from app.services.availability import AvailableSlot, InternalSchedulingProvider, SchedulingProvider
from app.services.errors import BusinessRuleViolation, DomainValidationError, ResourceNotFound
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
    exception_type: Literal["blocked", "unavailable"]
    reason: str | None = None

    @model_validator(mode="after")
    def validate_range_fields(self) -> "CreateAvailabilityExceptionRequest":
        if self.starts_at >= self.ends_at:
            raise ValueError("starts_at must be before ends_at")
        return self


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


def serialize_availability_exception(exception: AvailabilityException) -> dict[str, object]:
    return {
        "id": str(exception.id),
        "practitioner_id": str(exception.practitioner_id),
        "location_id": str(exception.location_id) if exception.location_id is not None else None,
        "room_id": str(exception.room_id) if exception.room_id is not None else None,
        "starts_at": exception.starts_at.isoformat(),
        "ends_at": exception.ends_at.isoformat(),
        "exception_type": exception.exception_type,
        "reason": exception.reason,
        "status": exception.status,
    }


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
    if session.get(Practitioner, payload.practitioner_id) is None:
        raise ResourceNotFound("Practitioner not found.")
    _validate_location_room(session, payload.location_id, payload.room_id)

    exception = AvailabilityException(**payload.model_dump())
    try:
        session.add(exception)
        session.flush()
        session.refresh(exception)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return {"data": serialize_availability_exception(exception)}


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
