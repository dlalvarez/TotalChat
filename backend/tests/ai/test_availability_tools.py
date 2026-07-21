from dataclasses import asdict
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.ai.availability_tools import AvailabilityRequest, AvailabilityTools
from app.models.tenant import (
    AvailabilityException,
    AvailabilityRule,
    Booking,
    Location,
    Organization,
    OrganizationPractitioner,
    Patient,
    Practitioner,
    PractitionerService,
    Room,
    ServiceModality,
)


TABLES = [
    Organization.__table__, Location.__table__, Room.__table__, Practitioner.__table__,
    OrganizationPractitioner.__table__, PractitionerService.__table__, ServiceModality.__table__,
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
    location = Location(organization=organization, name="Norte", status="active")
    room = Room(location=location, name="101", status="active")
    service = PractitionerService(
        organization=organization, practitioner=practitioner, name="Consulta",
        duration_minutes=30, status="active",
    )
    patient = Patient(full_name="Paciente")
    session.add_all([organization, practitioner, location, room, service, patient])
    session.flush()
    relation = OrganizationPractitioner(
        organization_id=organization.id, practitioner_id=practitioner.id, status="active",
    )
    modality = ServiceModality(
        practitioner_service_id=service.id, modality="in_person",
        location_id=location.id, room_id=room.id, status="active",
    )
    rule = AvailabilityRule(
        organization_id=organization.id, practitioner_id=practitioner.id,
        practitioner_service_id=service.id, location_id=location.id, room_id=room.id,
        modality="in_person", weekday=1, start_time=time(9), end_time=time(11),
        valid_from=date(2026, 7, 1), status="active",
    )
    session.add_all([relation, modality, rule])
    session.commit()
    yield session, organization, practitioner, location, room, service, patient, relation, rule
    session.close()
    engine.dispose()


def request(catalog, **changes) -> AvailabilityRequest:
    _, org, practitioner, location, room, service, *_ = catalog
    values = dict(
        practitioner_service_id=service.id, practitioner_id=practitioner.id,
        organization_id=org.id, modality="in_person", location_id=location.id,
        room_id=room.id, starts_on=date(2026, 7, 13), ends_on=date(2026, 7, 13), slot_limit=10,
    )
    values.update(changes)
    return AvailabilityRequest(**values)


def slots(catalog, **changes):
    return AvailabilityTools(tenant_id=uuid4(), session=catalog[0]).get_available_slots(request(catalog, **changes)).slots


def add_booking(catalog, *, status: str, starts_at: datetime = datetime(2026, 7, 13, 9, 30)) -> None:
    session, org, practitioner, location, room, service, patient, *_ = catalog
    session.add(Booking(
        organization_id=org.id, patient_id=patient.id, practitioner_id=practitioner.id,
        practitioner_service_id=service.id, location_id=location.id, room_id=room.id,
        modality="in_person", starts_at=starts_at, ends_at=starts_at + timedelta(minutes=30),
        status=status, service_name_snapshot=service.name, duration_minutes_snapshot=30,
        practitioner_name_snapshot=practitioner.full_name, modality_snapshot="in_person",
        price_snapshot=Decimal("1"), currency_snapshot="COP", total_amount=Decimal("1"),
    ))
    session.commit()


def test_generates_structured_slots_from_active_recurring_rules(catalog) -> None:
    result = slots(catalog)
    assert [(slot.starts_at.time(), slot.ends_at.time()) for slot in result] == [
        (time(9), time(9, 30)), (time(9, 30), time(10)),
        (time(10), time(10, 30)), (time(10, 30), time(11)),
    ]
    assert all(slot.modality == "in_person" for slot in result)


@pytest.mark.parametrize("resource", ["service", "practitioner", "organization", "relation"])
def test_inactive_domain_context_returns_no_slots(catalog, resource: str) -> None:
    indexes = {"organization": 1, "practitioner": 2, "service": 5, "relation": 7}
    setattr(catalog[indexes[resource]], "status", "inactive")
    catalog[0].commit()
    assert slots(catalog) == ()


def test_filters_modality_and_requires_matching_active_place(catalog) -> None:
    assert slots(catalog, modality="virtual", location_id=None, room_id=None) == ()
    catalog[4].status = "inactive"
    catalog[0].commit()
    assert slots(catalog) == ()


def test_general_rules_apply_when_request_targets_specific_active_place(catalog) -> None:
    session, _, _, location, room, _, _, _, rule = catalog
    rule.location_id = None
    rule.room_id = None
    session.commit()

    result = slots(catalog)

    assert result
    assert {slot.location_id for slot in result} == {location.id}
    assert {slot.room_id for slot in result} == {room.id}


def test_general_rule_does_not_apply_to_place_without_matching_service_modality(catalog) -> None:
    session, organization, _, _, _, _, _, _, rule = catalog
    other_location = Location(organization=organization, name="Sur", status="active")
    other_room = Room(location=other_location, name="202", status="active")
    rule.location_id = None
    rule.room_id = None
    session.add_all([other_location, other_room])
    session.commit()

    result = slots(catalog, location_id=other_location.id, room_id=other_room.id)

    assert result == ()


def test_active_exception_removes_overlapping_slots(catalog) -> None:
    session, _, practitioner, location, room, *_ = catalog
    session.add(AvailabilityException(
        practitioner_id=practitioner.id, location_id=location.id, room_id=room.id,
        starts_at=datetime(2026, 7, 13, 9, 15), ends_at=datetime(2026, 7, 13, 9, 45),
        exception_type="unavailable", status="active",
    ))
    session.commit()
    assert [slot.starts_at.time() for slot in slots(catalog)] == [time(10), time(10, 30)]


@pytest.mark.parametrize("status", ["tentative", "pending_payment", "confirmed", "rescheduled"])
def test_blocking_booking_statuses_remove_occupied_slot(catalog, status: str) -> None:
    add_booking(catalog, status=status)
    assert time(9, 30) not in [slot.starts_at.time() for slot in slots(catalog)]


@pytest.mark.parametrize("status", ["cancelled", "cancelled_by_patient", "expired", "completed", "no_show"])
def test_terminal_booking_statuses_do_not_remove_slot(catalog, status: str) -> None:
    add_booking(catalog, status=status)
    assert time(9, 30) in [slot.starts_at.time() for slot in slots(catalog)]


def test_overlapping_equivalent_rules_are_deduplicated_and_limit_is_respected(catalog) -> None:
    session, org, practitioner, location, room, service, _, _, rule = catalog
    session.add(AvailabilityRule(
        organization_id=org.id, practitioner_id=practitioner.id, practitioner_service_id=service.id,
        location_id=location.id, room_id=room.id, modality="in_person", weekday=rule.weekday,
        start_time=rule.start_time, end_time=rule.end_time, valid_from=rule.valid_from, status="active",
    ))
    session.commit()
    assert len(slots(catalog, slot_limit=2)) == 2


def test_result_excludes_schema_price_payment_and_mutating_data(catalog) -> None:
    fields = asdict(slots(catalog, slot_limit=1)[0])
    assert "schema_name" not in fields
    assert "price" not in fields
    assert "payment" not in fields
    assert "booking_id" not in fields


def test_tool_requires_resolved_tenant_and_local_repository_or_session() -> None:
    with pytest.raises(ValueError, match="tenant-scoped repository or session"):
        AvailabilityTools(tenant_id=uuid4())
    annotations = AvailabilityTools.__init__.__annotations__
    assert "schema_name" not in annotations
    assert "llm" not in annotations
    assert "client" not in annotations


def test_request_validation_is_deterministic(catalog) -> None:
    with pytest.raises(ValueError, match="location_id"):
        request(catalog, location_id=None)
    with pytest.raises(ValueError, match="slot_limit"):
        request(catalog, slot_limit=0)
    assert isinstance(request(catalog).practitioner_service_id, UUID)
