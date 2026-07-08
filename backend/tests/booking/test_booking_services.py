from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

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
    ServiceModality,
    Specialty,
)
from app.services.booking import BookingService, BookingSnapshotBuilder, BookingTransitionService, PriceResolution, PricingService
from app.services.errors import BusinessRuleViolation, DomainValidationError, PricingNotFound
from app.tenancy.context import TenantContext

TENANT_TABLES = [
    Organization.__table__, Location.__table__, Room.__table__, Practitioner.__table__, Specialty.__table__,
    PractitionerService.__table__, ServiceModality.__table__, PayerType.__table__, Payer.__table__, PayerPlan.__table__,
    PractitionerServicePrice.__table__, Patient.__table__, Booking.__table__,
]


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:")
    for table in TENANT_TABLES:
        table.create(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture()
def booking_fixture(session):
    org = Organization(name="Clínica Vida", organization_type="clinic")
    loc = Location(organization=org, name="Sede Norte", address="Calle 123")
    room = Room(location=loc, name="Consultorio 301")
    practitioner = Practitioner(full_name="Dra. Ana Pérez", status="active")
    service = PractitionerService(organization=org, practitioner=practitioner, name="Consulta psicológica", duration_minutes=50, status="active")
    payer_type = PayerType(code="particular", name="Particular", status="active")
    payer = Payer(payer_type=payer_type, name="Particular", status="active")
    plan = PayerPlan(payer=payer, name="Tarifa particular", status="active")
    price = PractitionerServicePrice(practitioner_service=service, payer_plan=plan, price=Decimal("120000.00"), currency="COP", valid_from=date(2026, 1, 1), status="active")
    session.add_all([org, loc, room, practitioner, service, payer_type, payer, plan, price])
    session.flush()
    modality = ServiceModality(practitioner_service_id=service.id, modality="in_person", location_id=loc.id, room_id=room.id, status="active")
    session.add(modality)
    session.flush()
    return org, loc, room, practitioner, service, payer_type, payer, plan, price


def test_pricing_service_resolves_price_by_practitioner_service_and_payer_plan(session, booking_fixture):
    *_, service, payer_type, payer, plan, _price = booking_fixture
    resolved = PricingService(session).resolve_price(service.id, plan.id, on_date=date(2026, 7, 8))
    assert resolved.price == Decimal("120000.00")
    assert resolved.currency == "COP"
    assert resolved.payer_type_name == payer_type.name
    assert resolved.payer_name == payer.name
    assert resolved.payer_plan_name == plan.name


def test_pricing_service_does_not_use_specialty_for_price(session, booking_fixture):
    *_, service, _payer_type, _payer, plan, _price = booking_fixture
    session.add(Specialty(name="Psicología", status="active"))
    session.flush()
    assert PricingService(session).resolve_price(service.id, plan.id, on_date=date(2026, 7, 8)).price == Decimal("120000.00")


def test_pricing_service_rejects_missing_price(session, booking_fixture):
    *_, service, _payer_type, _payer, _plan, _price = booking_fixture
    with pytest.raises(PricingNotFound):
        PricingService(session).resolve_price(service.id, uuid4(), on_date=date(2026, 7, 8))


def test_booking_snapshot_builder_creates_immutable_snapshot_payload(booking_fixture):
    org, loc, room, practitioner, service, payer_type, payer, plan, _price = booking_fixture
    resolution = PriceResolution(Decimal("120000.00"), "COP", payer_type.id, payer_type.name, payer.id, payer.name, plan.id, plan.name)
    snapshot = BookingSnapshotBuilder().build(practitioner_service=service, practitioner=practitioner, organization_name=org.name, modality="in_person", location=loc, room=room, price_resolution=resolution)
    service.name = "Consulta modificada"
    plan.name = "Plan modificado"
    assert snapshot["service_name_snapshot"] == "Consulta psicológica"
    assert snapshot["payer_plan_name_snapshot"] == "Tarifa particular"
    assert snapshot["address_snapshot"] == "Calle 123"
    assert snapshot["room_snapshot"] == "Consultorio 301"


def test_booking_state_machine_allows_documented_transitions_and_rejects_prohibited_transitions():
    machine = BookingTransitionService()
    for current, targets in machine.ALLOWED_TRANSITIONS.items():
        for target in targets:
            machine.validate_transition(current, target)
    with pytest.raises(BusinessRuleViolation):
        machine.validate_transition("confirmed", "tentative")
    with pytest.raises(BusinessRuleViolation):
        machine.validate_transition("expired_no_evidence", "confirmed")
    with pytest.raises(BusinessRuleViolation):
        machine.validate_transition("cancelled_by_admin", "confirmed")


def test_booking_service_creates_tentative_booking_with_snapshot(session, booking_fixture):
    org, loc, room, practitioner, service, payer_type, payer, plan, _price = booking_fixture
    tenant_context = TenantContext(tenant_id=uuid4(), slug="clinica-vida", schema_name="tenant_clinica_vida")
    booking = BookingService(session, tenant_context).create_tentative_booking(
        practitioner_service_id=service.id,
        payer_plan_id=plan.id,
        starts_at=datetime(2026, 7, 10, 14, 0, tzinfo=timezone.utc),
        modality="in_person",
        location_id=loc.id,
        room_id=room.id,
        patient_data={"full_name": "Paciente Uno", "created_from_channel": "web"},
        created_channel="web",
    )
    assert booking.status == "tentative"
    assert booking.organization_id == org.id
    assert booking.patient_id is not None
    assert booking.service_name_snapshot == service.name
    assert booking.practitioner_name_snapshot == practitioner.full_name
    assert booking.payer_type_name_snapshot == payer_type.name
    assert booking.payer_name_snapshot == payer.name
    assert booking.payer_plan_name_snapshot == plan.name
    assert booking.price_snapshot == Decimal("120000.00")
    assert booking.total_amount == Decimal("120000.00")
    assert booking.address_snapshot == loc.address
    assert booking.room_snapshot == room.name


def test_booking_service_requires_tenant_context(session):
    with pytest.raises(DomainValidationError):
        BookingService(session, None)  # type: ignore[arg-type]
