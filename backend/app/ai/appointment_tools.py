"""Tenant-scoped appointment tools for the booking agent."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.availability_tools import AvailabilityRequest, SQLAlchemyAvailabilityRepository
from app.models.tenant import (
    Booking,
    Location,
    Organization,
    Patient,
    Payer,
    PayerPlan,
    PayerType,
    Practitioner,
    PractitionerService,
    PractitionerServicePrice,
    Room,
)
from app.services.errors import ResourceNotFound, SlotNotAvailable


@dataclass(frozen=True, slots=True)
class AppointmentRequest:
    patient_id: UUID
    practitioner_service_id: UUID
    practitioner_id: UUID
    organization_id: UUID
    payer_plan_id: UUID
    modality: str
    starts_at: datetime
    ends_at: datetime
    location_id: UUID | None = None
    room_id: UUID | None = None

    def __post_init__(self) -> None:
        if self.modality not in {"in_person", "virtual"}:
            raise ValueError("modality must be in_person or virtual")
        if self.starts_at >= self.ends_at:
            raise ValueError("starts_at must be before ends_at")
        if self.modality == "in_person" and self.location_id is None:
            raise ValueError("location_id is required for in_person appointments")
        if self.room_id is not None and self.location_id is None:
            raise ValueError("location_id is required when room_id is provided")


@dataclass(frozen=True, slots=True)
class AppointmentResult:
    appointment_id: UUID
    status: str
    starts_at: datetime
    ends_at: datetime
    practitioner_id: UUID
    practitioner_service_id: UUID
    organization_id: UUID
    location_id: UUID | None
    room_id: UUID | None
    modality: str


class AppointmentRepository(Protocol):
    """Port bound to storage for exactly one already-resolved tenant."""

    def create(self, request: AppointmentRequest) -> AppointmentResult: ...

    def get(self, appointment_id: UUID) -> AppointmentResult | None: ...


class SQLAlchemyAppointmentRepository:
    """Creates real booking occupancy through a tenant-scoped session."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._availability = SQLAlchemyAvailabilityRepository(session)

    def create(self, request: AppointmentRequest) -> AppointmentResult:
        # Serialize competing creates for a practitioner on PostgreSQL. The
        # availability check and insert intentionally happen in one transaction.
        practitioner = self._session.scalar(
            select(Practitioner).where(Practitioner.id == request.practitioner_id).with_for_update()
        )
        if practitioner is None:
            raise ResourceNotFound("Practitioner not found")

        available = self._availability.list_available(
            AvailabilityRequest(
                practitioner_service_id=request.practitioner_service_id,
                practitioner_id=request.practitioner_id,
                organization_id=request.organization_id,
                modality=request.modality,
                starts_on=request.starts_at.date(),
                ends_on=request.starts_at.date(),
                location_id=request.location_id,
                room_id=request.room_id,
                slot_limit=100,
            )
        )
        if not any(slot.starts_at == request.starts_at and slot.ends_at == request.ends_at for slot in available):
            raise SlotNotAvailable("Requested slot is not currently available")

        patient = self._session.get(Patient, request.patient_id)
        if patient is None:
            raise ResourceNotFound("Patient not found")
        service = self._session.get(PractitionerService, request.practitioner_service_id)
        organization = self._session.get(Organization, request.organization_id)
        location = self._session.get(Location, request.location_id) if request.location_id else None
        room = self._session.get(Room, request.room_id) if request.room_id else None
        price_row = self._session.execute(
            select(PractitionerServicePrice, PayerPlan, Payer, PayerType)
            .join(PayerPlan, PayerPlan.id == PractitionerServicePrice.payer_plan_id)
            .join(Payer, Payer.id == PayerPlan.payer_id)
            .join(PayerType, PayerType.id == Payer.payer_type_id)
            .where(
                PractitionerServicePrice.practitioner_service_id == request.practitioner_service_id,
                PractitionerServicePrice.payer_plan_id == request.payer_plan_id,
                PractitionerServicePrice.status == "active",
                PayerPlan.status == "active",
                Payer.status == "active",
                PayerType.status == "active",
                PractitionerServicePrice.valid_from <= request.starts_at.date(),
                (PractitionerServicePrice.valid_to.is_(None))
                | (PractitionerServicePrice.valid_to >= request.starts_at.date()),
            )
            .order_by(PractitionerServicePrice.valid_from.desc())
            .limit(1)
        ).first()
        if price_row is None:
            raise ResourceNotFound("Active payer plan price not found")
        price, plan, payer, payer_type = price_row
        assert service is not None and organization is not None

        booking = Booking(
            organization_id=organization.id,
            patient_id=patient.id,
            practitioner_id=practitioner.id,
            practitioner_service_id=service.id,
            payer_type_id=payer_type.id,
            payer_id=payer.id,
            payer_plan_id=plan.id,
            location_id=request.location_id,
            room_id=request.room_id,
            modality=request.modality,
            starts_at=request.starts_at,
            ends_at=request.ends_at,
            status="tentative",
            service_name_snapshot=service.name,
            duration_minutes_snapshot=service.duration_minutes,
            practitioner_name_snapshot=practitioner.full_name,
            modality_snapshot=request.modality,
            location_name_snapshot=location.name if location else None,
            address_snapshot=location.address if location else None,
            room_snapshot=room.name if room else None,
            payer_type_name_snapshot=payer_type.name,
            payer_name_snapshot=payer.name,
            payer_plan_name_snapshot=plan.name,
            price_snapshot=price.price,
            currency_snapshot=price.currency,
            total_amount=price.price,
            pending_patient_data=patient.profile_status != "complete",
        )
        self._session.add(booking)
        self._session.flush()
        return self._result(booking)

    def get(self, appointment_id: UUID) -> AppointmentResult | None:
        booking = self._session.get(Booking, appointment_id)
        return self._result(booking) if booking is not None else None

    @staticmethod
    def _result(booking: Booking) -> AppointmentResult:
        return AppointmentResult(
            appointment_id=booking.id,
            status=booking.status,
            starts_at=booking.starts_at,
            ends_at=booking.ends_at,
            practitioner_id=booking.practitioner_id,
            practitioner_service_id=booking.practitioner_service_id,
            organization_id=booking.organization_id,
            location_id=booking.location_id,
            room_id=booking.room_id,
            modality=booking.modality,
        )


class AppointmentTools:
    """Structured appointment commands for an already-resolved tenant."""

    def __init__(
        self,
        *,
        tenant_id: UUID,
        repository: AppointmentRepository | None = None,
        session: Session | None = None,
    ) -> None:
        if not isinstance(tenant_id, UUID):
            raise TypeError("tenant_id must be a backend-resolved UUID")
        if repository is None and session is None:
            raise ValueError("a tenant-scoped repository or session is required")
        if repository is not None and session is not None:
            raise ValueError("provide repository or session, not both")
        self._tenant_id = tenant_id
        self._repository = repository or SQLAlchemyAppointmentRepository(session)  # type: ignore[arg-type]

    def create_appointment(self, request: AppointmentRequest) -> AppointmentResult:
        return self._repository.create(request)

    def get_appointment(self, appointment_id: UUID) -> AppointmentResult | None:
        return self._repository.get(appointment_id)
