from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.models.tenant import (
    Booking,
    Location,
    Patient,
    Payer,
    PayerPlan,
    PayerType,
    Practitioner,
    PractitionerService,
    PractitionerServicePrice,
    Room,
    ServiceModality,
)
from app.services.errors import BusinessRuleViolation, DomainValidationError, PricingNotFound, ResourceNotFound
from app.services.availability import InternalSchedulingProvider, SchedulingProvider
from app.tenancy.context import TenantContext


@dataclass(frozen=True, slots=True)
class PriceResolution:
    price: Decimal
    currency: str
    payer_type_id: UUID
    payer_type_name: str
    payer_id: UUID
    payer_name: str
    payer_plan_id: UUID
    payer_plan_name: str


class PricingService:
    """Resolve active prices from practitioner_service + payer_plan only."""

    def __init__(self, session: Session):
        self.session = session

    def resolve_price(self, practitioner_service_id: UUID, payer_plan_id: UUID, *, on_date: date | None = None) -> PriceResolution:
        effective_date = on_date or date.today()
        stmt = (
            select(PractitionerServicePrice, PayerPlan, Payer, PayerType)
            .join(PayerPlan, PractitionerServicePrice.payer_plan_id == PayerPlan.id)
            .join(Payer, PayerPlan.payer_id == Payer.id)
            .join(PayerType, Payer.payer_type_id == PayerType.id)
            .where(
                PractitionerServicePrice.practitioner_service_id == practitioner_service_id,
                PractitionerServicePrice.payer_plan_id == payer_plan_id,
                PractitionerServicePrice.status == "active",
                PayerPlan.status == "active",
                Payer.status == "active",
                PayerType.status == "active",
                PractitionerServicePrice.valid_from <= effective_date,
                or_(PractitionerServicePrice.valid_to.is_(None), PractitionerServicePrice.valid_to >= effective_date),
            )
            .order_by(PractitionerServicePrice.valid_from.desc())
            .limit(1)
        )
        row = self.session.execute(stmt).first()
        if row is None:
            raise PricingNotFound("No active price found for practitioner service and payer plan")
        price, plan, payer, payer_type = row
        return PriceResolution(
            price=price.price,
            currency=price.currency,
            payer_type_id=payer_type.id,
            payer_type_name=payer_type.name,
            payer_id=payer.id,
            payer_name=payer.name,
            payer_plan_id=plan.id,
            payer_plan_name=plan.name,
        )


class PatientService:
    def __init__(self, session: Session):
        self.session = session

    def get_or_create_minimal_patient(self, *, patient_id: UUID | None = None, patient: Patient | None = None, patient_data: dict | None = None) -> Patient:
        if patient is not None:
            if patient.id is None:
                self.session.add(patient)
            return patient
        if patient_id is not None:
            existing = self.session.get(Patient, patient_id)
            if existing is None:
                raise ResourceNotFound("Patient not found")
            return existing
        data = dict(patient_data or {})
        full_name = (data.get("full_name") or "").strip()
        if not full_name:
            raise DomainValidationError("Minimal patient data requires full_name")
        new_patient = Patient(
            full_name=full_name,
            phone=data.get("phone"),
            email=data.get("email"),
            document_type=data.get("document_type"),
            document_number=data.get("document_number"),
            profile_status=data.get("profile_status") or "minimal",
            created_from_channel=data.get("created_from_channel"),
        )
        self.session.add(new_patient)
        return new_patient

    def update_minimal_patient(self, patient: Patient, patient_data: dict) -> Patient:
        for field in ("full_name", "phone", "email", "document_type", "document_number", "created_from_channel"):
            if field in patient_data and patient_data[field] is not None:
                setattr(patient, field, patient_data[field])
        if not patient.profile_status:
            patient.profile_status = "minimal"
        return patient


class BookingSnapshotBuilder:
    def build(
        self,
        *,
        practitioner_service: PractitionerService,
        practitioner: Practitioner,
        organization_name: str | None = None,
        modality: str,
        location: Location | None,
        room: Room | None,
        price_resolution: PriceResolution,
    ) -> dict:
        _ = organization_name  # organization is included through booking FK; snapshot stores configured commercial/slot truth.
        return {
            "service_name_snapshot": practitioner_service.name,
            "duration_minutes_snapshot": practitioner_service.duration_minutes,
            "practitioner_name_snapshot": practitioner.full_name,
            "modality_snapshot": modality,
            "location_name_snapshot": location.name if location else None,
            "payer_type_name_snapshot": price_resolution.payer_type_name,
            "payer_name_snapshot": price_resolution.payer_name,
            "payer_plan_name_snapshot": price_resolution.payer_plan_name,
            "price_snapshot": price_resolution.price,
            "currency_snapshot": price_resolution.currency,
            "total_amount": price_resolution.price,
            "address_snapshot": location.address if location else None,
            "room_snapshot": room.name if room else None,
        }


class BookingTransitionService:
    ALLOWED_TRANSITIONS = {
        "draft": {"tentative"},
        "tentative": {"pending_payment", "confirmed_without_payment", "confirmed", "cancelled_by_admin", "expired"},
        "pending_payment": {"pending_payment_evidence", "confirmed", "confirmed_without_payment", "cancelled_by_patient", "cancelled_by_admin", "expired"},
        "pending_payment_evidence": {"pending_manual_payment_review", "expired_no_evidence", "cancelled_by_patient", "cancelled_by_admin"},
        "pending_manual_payment_review": {"confirmed", "rejected_payment", "review_overdue", "cancelled_by_admin"},
        "review_overdue": {"confirmed", "rejected_payment", "pending_manual_payment_review", "cancelled_by_admin"},
        "confirmed": {"cancelled_by_patient", "cancelled_by_admin", "rescheduled", "completed", "no_show", "auto_cancelled_no_confirmation"},
        "confirmed_without_payment": {"cancelled_by_patient", "cancelled_by_admin", "rescheduled", "completed", "no_show", "auto_cancelled_no_confirmation"},
        "rescheduled": {"confirmed", "cancelled_by_patient", "cancelled_by_admin"},
        "rejected_payment": {"pending_payment", "cancelled_by_admin", "expired"},
    }
    TERMINAL_STATES = {"cancelled_by_patient", "cancelled_by_admin", "completed", "no_show", "expired_no_evidence", "expired", "auto_cancelled_no_confirmation"}

    def validate_transition(self, current_status: str, new_status: str) -> None:
        if current_status in self.TERMINAL_STATES or new_status not in self.ALLOWED_TRANSITIONS.get(current_status, set()):
            raise BusinessRuleViolation(f"Invalid booking status transition: {current_status} -> {new_status}")

    PAYMENT_SATISFIED_STATUSES = {"approved", "paid"}

    def transition(self, booking: Booking, new_status: str) -> Booking:
        self.validate_transition(booking.status, new_status)
        booking.status = new_status
        return booking

    def confirm_booking(self, booking: Booking, practitioner_service: PractitionerService) -> Booking:
        if practitioner_service.requires_payment:
            if booking.payment_status not in self.PAYMENT_SATISFIED_STATUSES:
                raise BusinessRuleViolation("Booking requires satisfied payment before confirmation")
            return self.transition(booking, "confirmed")
        return self.transition(booking, "confirmed_without_payment")

    def cancel_booking_by_admin(self, booking: Booking, *, reason: str, release_slot: bool = True) -> Booking:
        if not reason.strip():
            raise DomainValidationError("Admin cancellation requires a reason")
        _ = release_slot  # Internal scheduling frees the slot by removing this booking from active statuses.
        booking.admin_cancellation_reason = reason.strip()
        return self.transition(booking, "cancelled_by_admin")

    def reschedule_booking_by_admin(self, booking: Booking, *, reason: str) -> Booking:
        if not reason.strip():
            raise DomainValidationError("Admin reschedule requires a reason")
        booking.admin_reschedule_reason = reason.strip()
        return self.transition(booking, "rescheduled")


class BookingService:
    def __init__(self, session: Session, tenant_context: TenantContext, scheduling_provider: SchedulingProvider | None = None):
        if tenant_context is None:
            raise DomainValidationError("BookingService requires explicit TenantContext")
        self.session = session
        self.tenant_context = tenant_context
        self.pricing_service = PricingService(session)
        self.patient_service = PatientService(session)
        self.snapshot_builder = BookingSnapshotBuilder()
        self.scheduling_provider = scheduling_provider or InternalSchedulingProvider()
        self.transition_service = BookingTransitionService()

    def create_tentative_booking(
        self,
        *,
        practitioner_service_id: UUID,
        payer_plan_id: UUID,
        starts_at: datetime,
        modality: str,
        patient_id: UUID | None = None,
        patient: Patient | None = None,
        patient_data: dict | None = None,
        location_id: UUID | None = None,
        room_id: UUID | None = None,
        created_channel: str | None = None,
    ) -> Booking:
        practitioner_service = self.session.get(PractitionerService, practitioner_service_id)
        if practitioner_service is None or practitioner_service.status != "active":
            raise ResourceNotFound("Practitioner service not found")
        practitioner = self.session.get(Practitioner, practitioner_service.practitioner_id)
        if practitioner is None or practitioner.status != "active":
            raise ResourceNotFound("Practitioner not found")
        location = self.session.get(Location, location_id) if location_id else None
        room = self.session.get(Room, room_id) if room_id else None
        if location_id and location is None:
            raise ResourceNotFound("Location not found")
        if room_id and room is None:
            raise ResourceNotFound("Room not found")
        self._validate_modality(practitioner_service_id, modality, location_id, room_id)
        ends_at = starts_at + timedelta(minutes=practitioner_service.duration_minutes)
        self.scheduling_provider.ensure_slot_available(self.session, starts_at=starts_at, ends_at=ends_at, practitioner_id=practitioner.id, location_id=location_id, room_id=room_id)
        resolved_price = self.pricing_service.resolve_price(practitioner_service_id, payer_plan_id, on_date=starts_at.date())
        patient_obj = self.patient_service.get_or_create_minimal_patient(patient_id=patient_id, patient=patient, patient_data=patient_data)
        self.session.flush()
        snapshot = self.snapshot_builder.build(practitioner_service=practitioner_service, practitioner=practitioner, organization_name=None, modality=modality, location=location, room=room, price_resolution=resolved_price)
        booking = Booking(
            organization_id=practitioner_service.organization_id,
            patient_id=patient_obj.id,
            practitioner_id=practitioner.id,
            practitioner_service_id=practitioner_service.id,
            payer_type_id=resolved_price.payer_type_id,
            payer_id=resolved_price.payer_id,
            payer_plan_id=resolved_price.payer_plan_id,
            location_id=location_id,
            room_id=room_id,
            modality=modality,
            starts_at=starts_at,
            ends_at=ends_at,
            status="tentative",
            created_channel=created_channel,
            pending_patient_data=True,
            **snapshot,
        )
        self.session.add(booking)
        self.session.flush()
        return booking

    def confirm_booking(self, booking_id: UUID) -> Booking:
        booking = self.session.get(Booking, booking_id)
        if booking is None:
            raise ResourceNotFound("Booking not found")
        practitioner_service = self.session.get(PractitionerService, booking.practitioner_service_id)
        if practitioner_service is None:
            raise ResourceNotFound("Practitioner service not found")
        return self.transition_service.confirm_booking(booking, practitioner_service)

    def cancel_booking_by_admin(self, booking_id: UUID, *, reason: str, release_slot: bool = True) -> Booking:
        booking = self.session.get(Booking, booking_id)
        if booking is None:
            raise ResourceNotFound("Booking not found")
        return self.transition_service.cancel_booking_by_admin(booking, reason=reason, release_slot=release_slot)

    def reschedule_booking_by_admin(self, booking_id: UUID, *, new_starts_at: datetime, new_location_id: UUID | None, new_room_id: UUID | None, reason: str) -> Booking:
        booking = self.session.get(Booking, booking_id)
        if booking is None:
            raise ResourceNotFound("Booking not found")
        practitioner_service = self.session.get(PractitionerService, booking.practitioner_service_id)
        if practitioner_service is None or practitioner_service.status != "active":
            raise ResourceNotFound("Practitioner service not found")
        practitioner = self.session.get(Practitioner, booking.practitioner_id)
        if practitioner is None or practitioner.status != "active":
            raise ResourceNotFound("Practitioner not found")
        location = self.session.get(Location, new_location_id) if new_location_id else None
        room = self.session.get(Room, new_room_id) if new_room_id else None
        if new_location_id and location is None:
            raise ResourceNotFound("Location not found")
        if new_room_id and room is None:
            raise ResourceNotFound("Room not found")

        self._validate_modality(practitioner_service.id, booking.modality, new_location_id, new_room_id)
        stripped_reason = reason.strip()
        if not stripped_reason:
            raise DomainValidationError("Admin reschedule requires a reason")
        self.transition_service.validate_transition(booking.status, "rescheduled")
        new_ends_at = new_starts_at + timedelta(minutes=practitioner_service.duration_minutes)

        self.scheduling_provider.ensure_slot_available(
            self.session,
            starts_at=new_starts_at,
            ends_at=new_ends_at,
            practitioner_id=booking.practitioner_id,
            location_id=new_location_id,
            room_id=new_room_id,
            exclude_booking_id=booking.id,
        )
        self.transition_service.reschedule_booking_by_admin(booking, reason=stripped_reason)
        booking.starts_at = new_starts_at
        booking.ends_at = new_ends_at
        booking.location_id = new_location_id
        booking.room_id = new_room_id
        booking.location_name_snapshot = location.name if location else None
        booking.address_snapshot = location.address if location else None
        booking.room_snapshot = room.name if room else None
        return booking

    def _validate_modality(self, practitioner_service_id: UUID, modality: str, location_id: UUID | None, room_id: UUID | None) -> None:
        stmt = select(ServiceModality).where(
            ServiceModality.practitioner_service_id == practitioner_service_id,
            ServiceModality.status == "active",
            ServiceModality.modality.in_([modality, "both"]),
        )
        constraints = []
        if location_id is not None:
            constraints.append(or_(ServiceModality.location_id.is_(None), ServiceModality.location_id == location_id))
        if room_id is not None:
            constraints.append(or_(ServiceModality.room_id.is_(None), ServiceModality.room_id == room_id))
        if constraints:
            stmt = stmt.where(and_(*constraints))
        if self.session.execute(stmt.limit(1)).scalar_one_or_none() is None:
            raise BusinessRuleViolation("Requested modality/location/room is not enabled for this practitioner service")
