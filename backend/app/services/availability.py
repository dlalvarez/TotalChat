from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Protocol
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.models.tenant import AvailabilityException, AvailabilityRule, Booking, PractitionerService, Room, ServiceModality
from app.services.errors import DomainValidationError, ResourceNotFound, SlotNotAvailable
from app.tenancy.context import TenantContext


@dataclass(frozen=True, slots=True)
class AvailableSlot:
    starts_at: datetime
    ends_at: datetime
    practitioner_id: UUID
    location_id: UUID | None
    room_id: UUID | None
    modality: str
    source: str = "internal"


@dataclass(frozen=True, slots=True)
class AvailableSlotsRequest:
    practitioner_service_id: UUID
    date_from: date
    date_to: date
    modality: str
    practitioner_id: UUID | None = None
    location_id: UUID | None = None
    room_id: UUID | None = None


class SchedulingProvider(Protocol):
    def get_available_slots(
        self,
        session: Session,
        tenant_context: TenantContext,
        request: AvailableSlotsRequest,
    ) -> list[AvailableSlot]: ...

    def list_available_slots(self, session: Session, tenant_context: TenantContext, **kwargs) -> list[AvailableSlot]: ...

    def ensure_slot_available(
        self,
        session: Session,
        *,
        starts_at: datetime,
        ends_at: datetime,
        practitioner_id: UUID,
        location_id: UUID | None = None,
        room_id: UUID | None = None,
        exclude_booking_id: UUID | None = None,
    ) -> None: ...


class AvailabilityService:
    """Tenant-scoped internal availability slot generation.

    Weekday convention follows ISO-8601: Monday=1 through Sunday=7.
    TenantContext must be supplied by trusted backend tenancy resolution; schema
    names are never accepted as service input.
    """

    MAX_DATE_RANGE_DAYS = 31

    def __init__(self, session: Session, tenant_context: TenantContext):
        if tenant_context is None:
            raise DomainValidationError("AvailabilityService requires explicit TenantContext")
        self.session = session
        self.tenant_context = tenant_context

    def list_available_slots(
        self,
        *,
        practitioner_service_id: UUID,
        start_date: date,
        end_date: date,
        modality: str,
        practitioner_id: UUID | None = None,
        location_id: UUID | None = None,
        room_id: UUID | None = None,
    ) -> list[AvailableSlot]:
        if start_date > end_date:
            raise DomainValidationError("start_date must be on or before end_date")
        if (end_date - start_date).days + 1 > self.MAX_DATE_RANGE_DAYS:
            raise DomainValidationError(f"availability date range cannot exceed {self.MAX_DATE_RANGE_DAYS} days")
        if modality not in {"in_person", "virtual"}:
            raise DomainValidationError("modality must be in_person or virtual")
        if room_id is not None and location_id is None:
            raise DomainValidationError("location_id is required when room_id is provided")
        if room_id is not None:
            room = self.session.get(Room, room_id)
            if room is None:
                raise ResourceNotFound("Room not found")
            if room.status != "active":
                raise DomainValidationError("room_id must reference an active room")
            if room.location_id != location_id:
                raise DomainValidationError("room_id must belong to location_id")
        practitioner_service = self.session.get(PractitionerService, practitioner_service_id)
        if practitioner_service is None or practitioner_service.status != "active":
            raise ResourceNotFound("Practitioner service not found")
        resolved_practitioner_id = practitioner_id or practitioner_service.practitioner_id
        if resolved_practitioner_id != practitioner_service.practitioner_id:
            raise DomainValidationError("practitioner_id must match practitioner_service")

        if not self._service_modality_enabled(practitioner_service_id, modality, location_id, room_id):
            return []

        slots: dict[tuple[object, ...], AvailableSlot] = {}
        current_date = start_date
        while current_date <= end_date:
            for rule in self._rules_for_date(
                organization_id=practitioner_service.organization_id,
                practitioner_service_id=practitioner_service_id,
                practitioner_id=resolved_practitioner_id,
                current_date=current_date,
                modality=modality,
                location_id=location_id,
                room_id=room_id,
            ):
                effective_location_id = location_id or rule.location_id
                effective_room_id = room_id or rule.room_id
                if not self._service_modality_enabled(
                    practitioner_service_id,
                    modality,
                    effective_location_id,
                    effective_room_id,
                ):
                    continue
                for slot in self._slots_for_rule(
                    rule,
                    current_date,
                    practitioner_service.duration_minutes,
                    requested_modality=modality,
                    requested_location_id=location_id,
                    requested_room_id=room_id,
                ):
                    key = (slot.starts_at, slot.ends_at, slot.practitioner_id, slot.location_id, slot.room_id, slot.modality)
                    slots[key] = slot
            current_date += timedelta(days=1)

        return [
            slot
            for slot in sorted(slots.values(), key=self._slot_sort_key)
            if not self._has_exception(slot) and not self._has_active_booking(slot)
        ]

    def _rules_for_date(self, *, organization_id: UUID, practitioner_service_id: UUID, practitioner_id: UUID, current_date: date, modality: str, location_id: UUID | None, room_id: UUID | None) -> list[AvailabilityRule]:
        stmt = select(AvailabilityRule).where(
            AvailabilityRule.status == "active",
            AvailabilityRule.organization_id == organization_id,
            AvailabilityRule.practitioner_id == practitioner_id,
            or_(AvailabilityRule.practitioner_service_id.is_(None), AvailabilityRule.practitioner_service_id == practitioner_service_id),
            AvailabilityRule.weekday == current_date.isoweekday(),
            AvailabilityRule.valid_from <= current_date,
            or_(AvailabilityRule.valid_to.is_(None), AvailabilityRule.valid_to >= current_date),
            AvailabilityRule.modality.in_([modality, "both"]),
        )
        if location_id is not None:
            stmt = stmt.where(or_(AvailabilityRule.location_id.is_(None), AvailabilityRule.location_id == location_id))
        if room_id is not None:
            stmt = stmt.where(or_(AvailabilityRule.room_id.is_(None), AvailabilityRule.room_id == room_id))
        return list(self.session.execute(stmt).scalars())

    def _slots_for_rule(
        self,
        rule: AvailabilityRule,
        current_date: date,
        duration_minutes: int,
        *,
        requested_modality: str,
        requested_location_id: UUID | None,
        requested_room_id: UUID | None,
    ) -> list[AvailableSlot]:
        cursor = datetime.combine(current_date, rule.start_time)
        rule_end = datetime.combine(current_date, rule.end_time)
        step = timedelta(minutes=duration_minutes + (rule.buffer_minutes or 0))
        duration = timedelta(minutes=duration_minutes)
        slots: list[AvailableSlot] = []
        while cursor + duration <= rule_end:
            slots.append(
                AvailableSlot(
                    cursor,
                    cursor + duration,
                    rule.practitioner_id,
                    requested_location_id or rule.location_id,
                    requested_room_id or rule.room_id,
                    requested_modality,
                )
            )
            cursor += step
        return slots

    @staticmethod
    def _slot_sort_key(slot: AvailableSlot) -> tuple[object, ...]:
        return (slot.starts_at, slot.ends_at, str(slot.practitioner_id), str(slot.location_id or ""), str(slot.room_id or ""), slot.modality)

    def _has_exception(self, slot: AvailableSlot) -> bool:
        stmt = select(AvailabilityException.id).where(
            AvailabilityException.status == "active",
            AvailabilityException.practitioner_id == slot.practitioner_id,
            AvailabilityException.starts_at < slot.ends_at,
            AvailabilityException.ends_at > slot.starts_at,
            or_(AvailabilityException.location_id.is_(None), AvailabilityException.location_id == slot.location_id),
            or_(AvailabilityException.room_id.is_(None), AvailabilityException.room_id == slot.room_id),
        )
        return self.session.execute(stmt.limit(1)).first() is not None

    def _has_active_booking(self, slot: AvailableSlot) -> bool:
        return InternalSchedulingProvider().slot_has_active_booking(self.session, slot)

    def _service_modality_enabled(self, practitioner_service_id: UUID, modality: str, location_id: UUID | None, room_id: UUID | None) -> bool:
        stmt = select(ServiceModality.id).where(
            ServiceModality.practitioner_service_id == practitioner_service_id,
            ServiceModality.status == "active",
            ServiceModality.modality.in_([modality, "both"]),
        )
        if location_id is not None:
            stmt = stmt.where(or_(ServiceModality.location_id.is_(None), ServiceModality.location_id == location_id))
        if room_id is not None:
            stmt = stmt.where(or_(ServiceModality.room_id.is_(None), ServiceModality.room_id == room_id))
        return self.session.execute(stmt.limit(1)).first() is not None


class InternalSchedulingProvider:
    ACTIVE_STATUSES = {"tentative", "pending_payment", "pending_payment_evidence", "pending_manual_payment_review", "review_overdue", "confirmed", "confirmed_without_payment", "rescheduled"}

    def get_available_slots(self, session: Session, tenant_context: TenantContext, request: AvailableSlotsRequest) -> list[AvailableSlot]:
        return AvailabilityService(session, tenant_context).list_available_slots(
            practitioner_service_id=request.practitioner_service_id,
            start_date=request.date_from,
            end_date=request.date_to,
            modality=request.modality,
            practitioner_id=request.practitioner_id,
            location_id=request.location_id,
            room_id=request.room_id,
        )

    def list_available_slots(self, session: Session, tenant_context: TenantContext, **kwargs) -> list[AvailableSlot]:
        return AvailabilityService(session, tenant_context).list_available_slots(**kwargs)

    def slot_has_active_booking(self, session: Session, slot: AvailableSlot, *, exclude_booking_id: UUID | None = None) -> bool:
        return self._overlapping_active_booking(session, starts_at=slot.starts_at, ends_at=slot.ends_at, practitioner_id=slot.practitioner_id, location_id=slot.location_id, room_id=slot.room_id, exclude_booking_id=exclude_booking_id)

    def ensure_slot_available(self, session: Session, *, starts_at: datetime, ends_at: datetime, practitioner_id: UUID, location_id: UUID | None = None, room_id: UUID | None = None, exclude_booking_id: UUID | None = None) -> None:
        if self._overlapping_active_booking(session, starts_at=starts_at, ends_at=ends_at, practitioner_id=practitioner_id, location_id=location_id, room_id=room_id, exclude_booking_id=exclude_booking_id):
            raise SlotNotAvailable("Requested slot overlaps an active booking")

    def _overlapping_active_booking(self, session: Session, *, starts_at: datetime, ends_at: datetime, practitioner_id: UUID, location_id: UUID | None, room_id: UUID | None, exclude_booking_id: UUID | None = None) -> bool:
        stmt = select(Booking.id).where(
            Booking.practitioner_id == practitioner_id,
            Booking.status.in_(self.ACTIVE_STATUSES),
            Booking.starts_at < ends_at,
            Booking.ends_at > starts_at,
        )
        if exclude_booking_id is not None:
            stmt = stmt.where(Booking.id != exclude_booking_id)
        if location_id is not None:
            stmt = stmt.where(or_(Booking.location_id.is_(None), Booking.location_id == location_id))
        if room_id is not None:
            stmt = stmt.where(or_(Booking.room_id.is_(None), Booking.room_id == room_id))
        return session.execute(stmt.limit(1)).first() is not None
