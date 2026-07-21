"""Deterministic simulated conversations for phase 7A.9."""

from dataclasses import asdict
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from app.ai.appointment_tools import AppointmentResult
from app.ai.availability_tools import AvailabilityToolResult, AvailableSlot
from app.ai.booking_agent import BookingAgent, BookingAgentStep, BookingConversationRequest
from app.ai.payment_tools import PaymentToolResult
from app.ai.pricing_tools import PriceQuote, PricingToolResult
from app.ai.service_tools import ServiceDetail, ServiceSummary, ServiceToolResult
from app.services.errors import BusinessRuleViolation, SlotNotAvailable


class Services:
    def __init__(self):
        self.service_id, self.practitioner_id, self.organization_id = uuid4(), uuid4(), uuid4()
        self.enabled = True

    def search_services(self, request):
        if not self.enabled:
            return ServiceToolResult(())
        return ServiceToolResult((ServiceSummary(
            self.service_id, "Consulta medicina general", None, 30,
            self.practitioner_id, "Dra. Ana", ("in_person",),
        ),))

    def get_service_detail(self, service_id):
        if not self.enabled or service_id != self.service_id:
            return None
        return ServiceDetail(
            self.service_id, "Consulta medicina general", None, 30,
            self.practitioner_id, "Dra. Ana", self.organization_id, "Centro", ("in_person",),
        )


class Pricing:
    def __init__(self, services):
        self.enabled = True
        self.plan_id = uuid4()
        self.service_id = services.service_id

    def get_pricing_options(self, request):
        if not self.enabled:
            return PricingToolResult(())
        return PricingToolResult((PriceQuote(
            uuid4(), self.service_id, self.plan_id, "Plan básico", uuid4(), "Sura",
            uuid4(), "Prepaid", Decimal("120000"), "COP", date(2026, 1, 1), None,
        ),))


class Availability:
    def __init__(self, services):
        self.enabled = True
        self.slot = AvailableSlot(
            datetime(2026, 7, 22, 9), datetime(2026, 7, 22, 9, 30),
            services.practitioner_id, services.service_id, services.organization_id,
            uuid4(), uuid4(), "in_person",
        )

    def get_available_slots(self, request):
        return AvailabilityToolResult((self.slot,) if self.enabled else ())


class Appointments:
    def __init__(self):
        self.fail_race = False
        self.created = []

    def create_appointment(self, request):
        if self.fail_race:
            raise SlotNotAvailable("occupied between availability and creation")
        self.created.append(request)
        return AppointmentResult(
            uuid4(), "tentative", request.starts_at, request.ends_at, request.practitioner_id,
            request.practitioner_service_id, request.organization_id, request.location_id,
            request.room_id, request.modality,
        )


class Payments:
    def __init__(self):
        self.allowed = {"transfer", "pay_on_site", "simulated"}
        self.terminal = False
        self.prepared = []

    def prepare_payment(self, request):
        if self.terminal:
            raise BusinessRuleViolation("Booking status does not allow payment preparation.")
        if request.method not in self.allowed:
            raise BusinessRuleViolation("Payment method is disabled")
        self.prepared.append(request)
        transfer = request.method == "transfer"
        return PaymentToolResult(
            request.booking_id, "tentative", "pending", Decimal("120000"), "COP", (),
            uuid4(), "evidence_required" if transfer else "pending", transfer, False,
        )


@pytest.fixture
def conversation():
    tenant_id = uuid4()
    services = Services()
    pricing = Pricing(services)
    availability = Availability(services)
    appointments = Appointments()
    payments = Payments()
    agent = BookingAgent(
        tenant_id=tenant_id, service_tools=services, pricing_tools=pricing,
        availability_tools=availability, appointment_tools=appointments,
        payment_tools=payments,
    )
    request = BookingConversationRequest(
        tenant_id=tenant_id, patient_id=uuid4(), service_query="consulta medicina general",
        practitioner_name="Dra. Ana", payer_type="prepaid", payer_name="Sura",
        plan_name="Plan básico", preferred_date=date(2026, 7, 22),
        preferred_modality="in_person", payment_method="transfer",
    )
    return agent, request, services, pricing, availability, appointments, payments


def test_complete_conversation_prepares_transfer_without_approving_or_releasing_slot(conversation):
    agent, request, _, _, _, appointments, payments = conversation
    result = agent.run(request)
    assert result.status == "booking_created_payment_prepared"
    assert result.completed_steps == tuple(BookingAgentStep)
    assert result.selected_service_name == "Consulta medicina general"
    assert result.selected_practitioner_name == "Dra. Ana"
    assert result.amount == Decimal("120000") and result.currency == "COP"
    assert result.payment_attempt_status == "evidence_required"
    assert result.requires_evidence is True
    assert result.payment_attempt_status not in {"approved", "simulated_approved"}
    assert len(appointments.created) == len(payments.prepared) == 1


@pytest.mark.parametrize("method", ["pay_on_site", "simulated"])
def test_allowed_non_transfer_payment_remains_pending(conversation, method):
    agent, request, *rest = conversation
    request = BookingConversationRequest(**{**asdict(request), "payment_method": method})
    result = agent.run(request)
    assert result.status == "booking_created_payment_prepared"
    assert result.payment_method == method and result.payment_attempt_status == "pending"
    assert result.requires_evidence is False


def test_no_active_applicable_service_creates_nothing(conversation):
    agent, request, services, _, _, appointments, payments = conversation
    services.enabled = False
    assert agent.run(request).status == "service_not_found"
    assert appointments.created == payments.prepared == []


def test_missing_configured_price_stops_before_availability_and_booking(conversation):
    agent, request, _, pricing, _, appointments, payments = conversation
    pricing.enabled = False
    result = agent.run(request)
    assert result.status == "price_not_configured"
    assert result.completed_steps == (BookingAgentStep.SERVICE,)
    assert appointments.created == payments.prepared == []


def test_no_availability_does_not_invent_or_create_a_slot(conversation):
    agent, request, _, _, availability, appointments, payments = conversation
    availability.enabled = False
    assert agent.run(request).status == "no_availability"
    assert appointments.created == payments.prepared == []


def test_slot_revalidated_as_occupied_is_not_booked(conversation):
    agent, request, _, _, _, appointments, payments = conversation
    appointments.fail_race = True
    result = agent.run(request)
    assert result.status == "slot_no_longer_available"
    assert BookingAgentStep.APPOINTMENT not in result.completed_steps
    assert appointments.created == payments.prepared == []


def test_disallowed_payment_method_creates_no_payment_attempt(conversation):
    agent, request, _, _, _, appointments, payments = conversation
    payments.allowed.remove("transfer")
    result = agent.run(request)
    assert result.status == "payment_not_prepared"
    assert len(appointments.created) == 1
    assert payments.prepared == []


def test_terminal_booking_is_never_prepared_or_automatically_changed(conversation):
    agent, request, _, _, _, appointments, payments = conversation
    payments.terminal = True
    result = agent.run(request)
    assert result.status == "payment_not_prepared"
    assert len(appointments.created) == 1 and payments.prepared == []
    assert result.payment_attempt_status is None


def test_contract_exposes_no_schema_llm_or_network_dependency(conversation):
    agent, request, *_ = conversation
    assert "schema_name" not in asdict(request)
    assert "schema_name" not in asdict(agent.run(request))
    annotations = BookingAgent.__init__.__annotations__
    assert all(name not in annotations for name in ("schema_name", "llm", "client", "http"))


def test_same_inputs_and_tool_truth_follow_the_same_steps(conversation):
    agent, request, *_ = conversation
    first = agent.run(request)
    second = agent.run(request)
    stable_fields = ("status", "completed_steps", "selected_service_name", "starts_at", "amount", "currency", "payment_attempt_status")
    assert tuple(getattr(first, field) for field in stable_fields) == tuple(getattr(second, field) for field in stable_fields)
