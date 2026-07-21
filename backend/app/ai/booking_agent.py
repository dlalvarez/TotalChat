"""Deterministic coordinator for simulated Booking Agent conversations.

This module deliberately contains no language-model, network, channel, or schema
resolution concerns.  It coordinates the existing structured tools after the
backend has resolved the tenant.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from app.ai.appointment_tools import AppointmentRequest, AppointmentTools
from app.ai.availability_tools import AvailabilityRequest, AvailabilityTools
from app.ai.payment_tools import PaymentPreparationRequest, PaymentTools
from app.ai.pricing_tools import PricingOptionsRequest, PricingTools
from app.ai.service_tools import ServiceSearchRequest, ServiceTools
from app.services.errors import BusinessRuleViolation, ResourceNotFound, SlotNotAvailable


class BookingAgentStep(StrEnum):
    SERVICE = "service"
    PRICE = "price"
    AVAILABILITY = "availability"
    APPOINTMENT = "appointment"
    PAYMENT = "payment"


@dataclass(frozen=True, slots=True)
class BookingConversationRequest:
    tenant_id: UUID
    patient_id: UUID
    service_query: str
    payer_type: str
    payer_name: str
    plan_name: str
    preferred_date: date
    preferred_modality: str
    payment_method: str
    practitioner_name: str | None = None
    location_id: UUID | None = None
    room_id: UUID | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.tenant_id, UUID):
            raise TypeError("tenant_id must be a backend-resolved UUID")
        if not self.service_query.strip():
            raise ValueError("service_query must not be blank")
        if self.preferred_modality not in {"in_person", "virtual"}:
            raise ValueError("preferred_modality must be in_person or virtual")


@dataclass(frozen=True, slots=True)
class BookingConversationResult:
    status: str
    completed_steps: tuple[BookingAgentStep, ...]
    selected_service_name: str | None = None
    selected_practitioner_name: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    amount: Decimal | None = None
    currency: str | None = None
    payment_method: str | None = None
    payment_attempt_status: str | None = None
    requires_evidence: bool = False
    appointment_id: UUID | None = None
    payment_attempt_id: UUID | None = None


class BookingAgent:
    """Coordinates one complete, deterministic booking conversation."""

    def __init__(
        self,
        *,
        tenant_id: UUID,
        service_tools: ServiceTools,
        pricing_tools: PricingTools,
        availability_tools: AvailabilityTools,
        appointment_tools: AppointmentTools,
        payment_tools: PaymentTools,
    ) -> None:
        if not isinstance(tenant_id, UUID):
            raise TypeError("tenant_id must be a backend-resolved UUID")
        self._tenant_id = tenant_id
        self._services = service_tools
        self._pricing = pricing_tools
        self._availability = availability_tools
        self._appointments = appointment_tools
        self._payments = payment_tools

    def run(self, request: BookingConversationRequest) -> BookingConversationResult:
        if request.tenant_id != self._tenant_id:
            raise ValueError("request tenant does not match the resolved agent tenant")
        steps: list[BookingAgentStep] = []

        services = self._services.search_services(
            ServiceSearchRequest(text=request.service_query, modality=request.preferred_modality)
        ).services
        normalized_practitioner = self._normalize(request.practitioner_name)
        if normalized_practitioner:
            services = tuple(
                item for item in services
                if normalized_practitioner in self._normalize(item.practitioner_name)
            )
        if not services:
            return BookingConversationResult("service_not_found", tuple(steps))
        service = services[0]
        detail = self._services.get_service_detail(service.service_id)
        if detail is None:
            return BookingConversationResult("service_not_found", tuple(steps))
        steps.append(BookingAgentStep.SERVICE)

        quotes = self._pricing.get_pricing_options(
            PricingOptionsRequest(service.service_id, as_of=request.preferred_date)
        ).prices
        quote = next(
            (
                item for item in quotes
                if self._normalize(item.payer_type_name) == self._normalize(request.payer_type)
                and self._normalize(item.payer_name) == self._normalize(request.payer_name)
                and self._normalize(item.payer_plan_name) == self._normalize(request.plan_name)
            ),
            None,
        )
        if quote is None:
            return self._partial("price_not_configured", steps, service.name, service.practitioner_name)
        steps.append(BookingAgentStep.PRICE)

        availability_request = AvailabilityRequest(
            practitioner_service_id=service.service_id,
            practitioner_id=service.practitioner_id,
            organization_id=detail.organization_id,
            modality=request.preferred_modality,
            starts_on=request.preferred_date,
            ends_on=request.preferred_date,
            location_id=request.location_id,
            room_id=request.room_id,
        )
        slots = self._availability.get_available_slots(availability_request).slots
        if not slots:
            return self._partial(
                "no_availability", steps, service.name, service.practitioner_name,
                amount=quote.amount, currency=quote.currency,
            )
        slot = slots[0]
        steps.append(BookingAgentStep.AVAILABILITY)

        try:
            appointment = self._appointments.create_appointment(
                AppointmentRequest(
                    patient_id=request.patient_id,
                    practitioner_service_id=service.service_id,
                    practitioner_id=service.practitioner_id,
                    organization_id=detail.organization_id,
                    payer_plan_id=quote.payer_plan_id,
                    modality=request.preferred_modality,
                    starts_at=slot.starts_at,
                    ends_at=slot.ends_at,
                    location_id=slot.location_id,
                    room_id=slot.room_id,
                )
            )
        except SlotNotAvailable:
            return self._partial(
                "slot_no_longer_available", steps, service.name, service.practitioner_name,
                starts_at=slot.starts_at, ends_at=slot.ends_at,
                amount=quote.amount, currency=quote.currency,
            )
        steps.append(BookingAgentStep.APPOINTMENT)

        try:
            payment = self._payments.prepare_payment(
                PaymentPreparationRequest(appointment.appointment_id, request.payment_method)
            )
        except (BusinessRuleViolation, ResourceNotFound):
            return self._partial(
                "payment_not_prepared", steps, service.name, service.practitioner_name,
                starts_at=appointment.starts_at, ends_at=appointment.ends_at,
                amount=quote.amount, currency=quote.currency,
                appointment_id=appointment.appointment_id,
            )
        steps.append(BookingAgentStep.PAYMENT)
        return BookingConversationResult(
            status="booking_created_payment_prepared",
            completed_steps=tuple(steps),
            selected_service_name=service.name,
            selected_practitioner_name=service.practitioner_name,
            starts_at=appointment.starts_at,
            ends_at=appointment.ends_at,
            amount=payment.amount,
            currency=payment.currency,
            payment_method=request.payment_method,
            payment_attempt_status=payment.attempt_status,
            requires_evidence=payment.requires_evidence,
            appointment_id=appointment.appointment_id,
            payment_attempt_id=payment.payment_attempt_id,
        )

    @staticmethod
    def _normalize(value: str | None) -> str:
        return (value or "").strip().casefold()

    @staticmethod
    def _partial(status: str, steps: list[BookingAgentStep], service: str, practitioner: str | None, **values: object) -> BookingConversationResult:
        return BookingConversationResult(
            status=status,
            completed_steps=tuple(steps),
            selected_service_name=service,
            selected_practitioner_name=practitioner,
            **values,  # type: ignore[arg-type]
        )
