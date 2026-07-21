from dataclasses import asdict
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.ai.appointment_tools import AppointmentRequest, AppointmentTools
from app.models.tenant import (
    AvailabilityException, AvailabilityRule, Booking, Location, Organization,
    OrganizationPractitioner, Patient, Payer, PayerPlan, PayerType, Practitioner,
    PractitionerService, PractitionerServicePrice, Room, ServiceModality,
)
from app.services.errors import SlotNotAvailable


TABLES = [
    Organization.__table__, Location.__table__, Room.__table__, Practitioner.__table__,
    OrganizationPractitioner.__table__, PractitionerService.__table__, ServiceModality.__table__,
    PayerType.__table__, Payer.__table__, PayerPlan.__table__, PractitionerServicePrice.__table__,
    Patient.__table__, AvailabilityRule.__table__, AvailabilityException.__table__, Booking.__table__,
]


@pytest.fixture
def catalog():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    for table in TABLES:
        table.create(engine)
    session = Session(engine)
    organization = Organization(name="Centro", organization_type="clinic", status="active")
    practitioner = Practitioner(full_name="Dra. Ana", status="active")
    location = Location(organization=organization, name="Norte", address="Calle 1", status="active")
    room = Room(location=location, name="101", status="active")
    service = PractitionerService(organization=organization, practitioner=practitioner, name="Consulta", duration_minutes=30, status="active")
    patient = Patient(full_name="Paciente")
    payer_type = PayerType(code="private", name="Particular", status="active")
    payer = Payer(payer_type=payer_type, name="Particular", status="active")
    plan = PayerPlan(payer=payer, name="Particular", status="active")
    session.add_all([organization, practitioner, location, room, service, patient, plan])
    session.flush()
    relation = OrganizationPractitioner(organization_id=organization.id, practitioner_id=practitioner.id, status="active")
    modality = ServiceModality(practitioner_service_id=service.id, modality="in_person", location_id=location.id, room_id=room.id, status="active")
    rule = AvailabilityRule(organization_id=organization.id, practitioner_id=practitioner.id, practitioner_service_id=service.id, location_id=location.id, room_id=room.id, modality="in_person", weekday=1, start_time=time(9), end_time=time(11), valid_from=date(2026, 7, 1), status="active")
    price = PractitionerServicePrice(practitioner_service_id=service.id, payer_plan_id=plan.id, price=Decimal("100000"), currency="COP", valid_from=date(2026, 1, 1), status="active")
    session.add_all([relation, modality, rule, price])
    session.commit()
    yield session, organization, practitioner, location, room, service, patient, plan, relation, modality
    session.close()
    engine.dispose()


def request(catalog, **changes):
    _, org, practitioner, location, room, service, patient, plan, *_ = catalog
    values = dict(patient_id=patient.id, practitioner_service_id=service.id, practitioner_id=practitioner.id, organization_id=org.id, payer_plan_id=plan.id, modality="in_person", starts_at=datetime(2026, 7, 13, 9), ends_at=datetime(2026, 7, 13, 9, 30), location_id=location.id, room_id=room.id)
    values.update(changes)
    return AppointmentRequest(**values)


def create(catalog, **changes):
    return AppointmentTools(tenant_id=uuid4(), session=catalog[0]).create_appointment(request(catalog, **changes))


def test_creates_and_reads_structured_tentative_appointment(catalog):
    result = create(catalog)
    assert result.status == "tentative"
    assert isinstance(result.appointment_id, UUID)
    assert AppointmentTools(tenant_id=uuid4(), session=catalog[0]).get_appointment(result.appointment_id) == result
    assert catalog[0].scalar(select(Booking).where(Booking.id == result.appointment_id)).payment_status == "pending"


def test_can_create_slot_after_first_100_available_slots(catalog):
    session, _, _, _, _, service, _, _, _, _ = catalog
    rule = session.scalar(select(AvailabilityRule))
    service.duration_minutes = 5
    rule.start_time = time(8)
    rule.end_time = time(20)
    session.commit()

    result = create(
        catalog,
        starts_at=datetime(2026, 7, 13, 18),
        ends_at=datetime(2026, 7, 13, 18, 5),
    )

    assert result.starts_at == datetime(2026, 7, 13, 18)
    assert result.ends_at == datetime(2026, 7, 13, 18, 5)


@pytest.mark.parametrize("index", [1, 2, 5, 8])
def test_inactive_domain_context_cannot_create(catalog, index):
    catalog[index].status = "inactive"
    catalog[0].commit()
    with pytest.raises(SlotNotAvailable):
        create(catalog)
    assert catalog[0].scalar(select(Booking.id)) is None


def test_inapplicable_modality_or_inactive_place_cannot_create(catalog):
    with pytest.raises(SlotNotAvailable):
        create(catalog, modality="virtual", location_id=None, room_id=None)
    catalog[4].status = "inactive"
    catalog[0].commit()
    with pytest.raises(SlotNotAvailable):
        create(catalog)


def test_active_exception_cannot_create(catalog):
    session, _, practitioner, location, room, *_ = catalog
    session.add(AvailabilityException(practitioner_id=practitioner.id, location_id=location.id, room_id=room.id, starts_at=datetime(2026, 7, 13, 8, 55), ends_at=datetime(2026, 7, 13, 9, 5), exception_type="unavailable", status="active"))
    session.commit()
    with pytest.raises(SlotNotAvailable):
        create(catalog)


def existing_booking(catalog, status):
    session, org, practitioner, location, room, service, patient, *_ = catalog
    session.add(Booking(organization_id=org.id, patient_id=patient.id, practitioner_id=practitioner.id, practitioner_service_id=service.id, location_id=location.id, room_id=room.id, modality="in_person", starts_at=datetime(2026, 7, 13, 9), ends_at=datetime(2026, 7, 13, 9, 30), status=status, service_name_snapshot=service.name, duration_minutes_snapshot=30, practitioner_name_snapshot=practitioner.full_name, modality_snapshot="in_person", price_snapshot=Decimal("1"), currency_snapshot="COP", total_amount=Decimal("1")))
    session.commit()


def test_blocking_booking_prevents_double_occupancy(catalog):
    existing_booking(catalog, "pending_payment")
    with pytest.raises(SlotNotAvailable):
        create(catalog)
    assert len(catalog[0].scalars(select(Booking)).all()) == 1


@pytest.mark.parametrize("status", ["cancelled_by_patient", "expired", "completed", "no_show"])
def test_nonblocking_booking_allows_appointment(catalog, status):
    existing_booking(catalog, status)
    assert create(catalog).status == "tentative"


def test_contract_exposes_neither_schema_payment_llm_nor_network(catalog):
    fields = asdict(create(catalog))
    assert "schema_name" not in fields
    assert not any("payment" in field for field in fields)
    annotations = AppointmentTools.__init__.__annotations__
    assert all(name not in annotations for name in ("schema_name", "llm", "client"))
    with pytest.raises(ValueError, match="tenant-scoped"):
        AppointmentTools(tenant_id=uuid4())


def test_request_validation_is_deterministic(catalog):
    with pytest.raises(ValueError, match="location_id"):
        request(catalog, location_id=None, room_id=None)
    with pytest.raises(ValueError, match="before"):
        request(catalog, ends_at=datetime(2026, 7, 13, 9))
