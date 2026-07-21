"""Tenant-scoped availability tools for the booking agent."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Protocol, Sequence
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.tenant import (
    AvailabilityException,
    AvailabilityRule,
    Booking,
    Location,
    Organization,
    OrganizationPractitioner,
    Practitioner,
    PractitionerService,
    Room,
    ServiceModality,
)
from app.services.availability import InternalSchedulingProvider


@dataclass(frozen=True, slots=True)
class AvailabilityRequest:
    practitioner_service_id: UUID
    practitioner_id: UUID
    organization_id: UUID
    modality: str
    starts_on: date
    ends_on: date
    location_id: UUID | None = None
    room_id: UUID | None = None
    slot_limit: int = 10

    def __post_init__(self) -> None:
        if self.modality not in {"in_person", "virtual"}:
            raise ValueError("modality must be in_person or virtual")
        if self.starts_on > self.ends_on:
            raise ValueError("starts_on must be on or before ends_on")
        if not 1 <= self.slot_limit <= 100:
            raise ValueError("slot_limit must be between 1 and 100")
        if self.room_id is not None and self.location_id is None:
            raise ValueError("location_id is required when room_id is provided")


@dataclass(frozen=True, slots=True)
class AvailableSlot:
    starts_at: datetime
    ends_at: datetime
    practitioner_id: UUID
    practitioner_service_id: UUID
    organization_id: UUID
    location_id: UUID | None
    room_id: UUID | None
    modality: str


@dataclass(frozen=True, slots=True)
class AvailabilityToolResult:
    slots: tuple[AvailableSlot, ...]


class AvailabilityRepository(Protocol):
    """Port bound to storage for one already-resolved tenant."""

    def list_available(self, request: AvailabilityRequest) -> Sequence[AvailableSlot]: ...


class SQLAlchemyAvailabilityRepository:
    """Calculates slots from authoritative data in a tenant-scoped session.

    The current domain stores rule times without a tenant timezone. Accordingly,
    datetimes are returned conservatively as tenant-local wall times (naive), just
    as the existing availability service does; no timezone is guessed.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_available(self, request: AvailabilityRequest) -> Sequence[AvailableSlot]:
        service = self._active_service(request)
        if service is None or not self._requested_resources_are_active(request):
            return ()

        candidates: dict[tuple[object, ...], AvailableSlot] = {}
        current = request.starts_on
        while current <= request.ends_on:
            for rule in self._rules(request, current):
                if not self._rule_resources_are_active(request, rule) or not self._rule_has_active_modality(request, rule):
                    continue
                for slot in self._slots(rule, current, service.duration_minutes, request):
                    key = (
                        slot.starts_at,
                        slot.ends_at,
                        slot.practitioner_id,
                        slot.practitioner_service_id,
                        slot.organization_id,
                        slot.location_id,
                        slot.room_id,
                        slot.modality,
                    )
                    candidates[key] = slot
            current += timedelta(days=1)

        available = [
            slot
            for slot in candidates.values()
            if not self._has_exception(slot) and not self._has_blocking_booking(slot)
        ]
        return tuple(sorted(available, key=self._sort_key)[: request.slot_limit])

    def _active_service(self, request: AvailabilityRequest) -> PractitionerService | None:
        return self._session.scalar(
            select(PractitionerService)
            .join(Practitioner, Practitioner.id == PractitionerService.practitioner_id)
            .join(Organization, Organization.id == PractitionerService.organization_id)
            .join(
                OrganizationPractitioner,
                (OrganizationPractitioner.organization_id == PractitionerService.organization_id)
                & (OrganizationPractitioner.practitioner_id == PractitionerService.practitioner_id),
            )
            .where(
                PractitionerService.id == request.practitioner_service_id,
                PractitionerService.practitioner_id == request.practitioner_id,
                PractitionerService.organization_id == request.organization_id,
                PractitionerService.status == "active",
                Practitioner.status == "active",
                Organization.status == "active",
                OrganizationPractitioner.status == "active",
            )
        )

    def _requested_resources_are_active(self, request: AvailabilityRequest) -> bool:
        if request.location_id is not None:
            location = self._session.scalar(
                select(Location).where(
                    Location.id == request.location_id,
                    Location.organization_id == request.organization_id,
                    Location.status == "active",
                )
            )
            if location is None:
                return False
        if request.room_id is not None:
            room = self._session.scalar(
                select(Room).where(
                    Room.id == request.room_id,
                    Room.location_id == request.location_id,
                    Room.status == "active",
                )
            )
            if room is None:
                return False
        return True

    def _rules(self, request: AvailabilityRequest, current: date) -> Sequence[AvailabilityRule]:
        query = select(AvailabilityRule).where(
            AvailabilityRule.status == "active",
            AvailabilityRule.organization_id == request.organization_id,
            AvailabilityRule.practitioner_id == request.practitioner_id,
            or_(
                AvailabilityRule.practitioner_service_id.is_(None),
                AvailabilityRule.practitioner_service_id == request.practitioner_service_id,
            ),
            AvailabilityRule.weekday == current.isoweekday(),
            AvailabilityRule.valid_from <= current,
            or_(AvailabilityRule.valid_to.is_(None), AvailabilityRule.valid_to >= current),
            AvailabilityRule.modality.in_([request.modality, "both"]),
        )
        if request.location_id is not None:
            query = query.where(
                or_(
                    AvailabilityRule.location_id.is_(None),
                    AvailabilityRule.location_id == request.location_id,
                )
            )
        if request.room_id is not None:
            query = query.where(
                or_(
                    AvailabilityRule.room_id.is_(None),
                    AvailabilityRule.room_id == request.room_id,
                )
            )
        return tuple(self._session.scalars(query))

    def _rule_resources_are_active(self, request: AvailabilityRequest, rule: AvailabilityRule) -> bool:
        if rule.location_id is not None and self._session.scalar(
            select(Location.id).where(
                Location.id == rule.location_id,
                Location.organization_id == request.organization_id,
                Location.status == "active",
            )
        ) is None:
            return False
        if rule.room_id is not None and self._session.scalar(
            select(Room.id).where(
                Room.id == rule.room_id,
                Room.location_id == rule.location_id,
                Room.status == "active",
            )
        ) is None:
            return False
        return True

    def _rule_has_active_modality(self, request: AvailabilityRequest, rule: AvailabilityRule) -> bool:
        query = select(ServiceModality.id).where(
            ServiceModality.practitioner_service_id == request.practitioner_service_id,
            ServiceModality.status == "active",
            ServiceModality.modality.in_([request.modality, "both"]),
        )
        if rule.location_id is not None:
            query = query.where(or_(ServiceModality.location_id.is_(None), ServiceModality.location_id == rule.location_id))
        if rule.room_id is not None:
            query = query.where(or_(ServiceModality.room_id.is_(None), ServiceModality.room_id == rule.room_id))
        return self._session.execute(query.limit(1)).first() is not None

    @staticmethod
    def _slots(
        rule: AvailabilityRule,
        current: date,
        duration_minutes: int,
        request: AvailabilityRequest,
    ) -> Sequence[AvailableSlot]:
        cursor = datetime.combine(current, rule.start_time)
        rule_end = datetime.combine(current, rule.end_time)
        duration = timedelta(minutes=duration_minutes)
        step = timedelta(minutes=duration_minutes + (rule.buffer_minutes or 0))
        slots: list[AvailableSlot] = []
        while cursor + duration <= rule_end:
            slots.append(
                AvailableSlot(
                    starts_at=cursor,
                    ends_at=cursor + duration,
                    practitioner_id=request.practitioner_id,
                    practitioner_service_id=request.practitioner_service_id,
                    organization_id=request.organization_id,
                    location_id=request.location_id or rule.location_id,
                    room_id=request.room_id or rule.room_id,
                    modality=request.modality,
                )
            )
            cursor += step
        return slots

    def _has_exception(self, slot: AvailableSlot) -> bool:
        query = select(AvailabilityException.id).where(
            AvailabilityException.status == "active",
            AvailabilityException.practitioner_id == slot.practitioner_id,
            AvailabilityException.starts_at < slot.ends_at,
            AvailabilityException.ends_at > slot.starts_at,
            or_(AvailabilityException.location_id.is_(None), AvailabilityException.location_id == slot.location_id),
            or_(AvailabilityException.room_id.is_(None), AvailabilityException.room_id == slot.room_id),
        )
        return self._session.execute(query.limit(1)).first() is not None

    def _has_blocking_booking(self, slot: AvailableSlot) -> bool:
        query = select(Booking.id).where(
            Booking.practitioner_id == slot.practitioner_id,
            Booking.status.in_(InternalSchedulingProvider.ACTIVE_STATUSES),
            Booking.starts_at < slot.ends_at,
            Booking.ends_at > slot.starts_at,
        )
        return self._session.execute(query.limit(1)).first() is not None

    @staticmethod
    def _sort_key(slot: AvailableSlot) -> tuple[object, ...]:
        return (
            slot.starts_at,
            slot.ends_at,
            str(slot.location_id or ""),
            str(slot.room_id or ""),
        )


class AvailabilityTools:
    """Read-only structured availability tools for an already-resolved tenant."""

    def __init__(
        self,
        *,
        tenant_id: UUID,
        repository: AvailabilityRepository | None = None,
        session: Session | None = None,
    ) -> None:
        if not isinstance(tenant_id, UUID):
            raise TypeError("tenant_id must be a backend-resolved UUID")
        if repository is None and session is None:
            raise ValueError("a tenant-scoped repository or session is required")
        if repository is not None and session is not None:
            raise ValueError("provide repository or session, not both")
        self._tenant_id = tenant_id
        self._repository = repository or SQLAlchemyAvailabilityRepository(session)  # type: ignore[arg-type]

    def get_available_slots(self, request: AvailabilityRequest) -> AvailabilityToolResult:
        return AvailabilityToolResult(tuple(self._repository.list_available(request)))
