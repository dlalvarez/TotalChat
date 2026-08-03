from datetime import date, datetime, time, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.models.tenant import AvailabilityException, AvailabilityRule, Booking, Location, Organization, Patient, Practitioner, PractitionerService, Room, ServiceModality
from app.services.availability import AvailabilityService, InternalSchedulingProvider
from app.services.errors import DomainValidationError, SlotNotAvailable
from app.tenancy.context import TenantContext

TENANT_TABLES = [Organization.__table__, Location.__table__, Room.__table__, Practitioner.__table__, PractitionerService.__table__, ServiceModality.__table__, Patient.__table__, AvailabilityRule.__table__, AvailabilityException.__table__, Booking.__table__]


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:")
    for table in TENANT_TABLES:
        table.create(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture()
def ctx():
    return TenantContext(tenant_id=uuid4(), slug="clinica-vida", schema_name="tenant_clinica_vida")


@pytest.fixture()
def availability_fixture(session):
    org = Organization(name="Clínica Vida", organization_type="clinic")
    loc = Location(organization=org, name="Sede Norte", address="Calle 123")
    room = Room(location=loc, name="Consultorio 301")
    practitioner = Practitioner(full_name="Dra. Ana Pérez", status="active")
    service = PractitionerService(organization=org, practitioner=practitioner, name="Consulta", duration_minutes=30, status="active")
    patient = Patient(full_name="Paciente Uno")
    session.add_all([org, loc, room, practitioner, service, patient])
    session.flush()
    session.add(ServiceModality(practitioner_service_id=service.id, modality="in_person", location_id=loc.id, room_id=room.id, status="active"))
    session.add(AvailabilityRule(organization_id=org.id, practitioner_id=practitioner.id, practitioner_service_id=None, location_id=loc.id, room_id=room.id, modality="in_person", weekday=1, start_time=time(9), end_time=time(10, 30), valid_from=date(2026, 7, 1), status="active"))
    session.flush()
    return org, loc, room, practitioner, service, patient


def list_slots(session, ctx, fixture, **overrides):
    _org, loc, room, practitioner, service, _patient = fixture
    params = dict(practitioner_service_id=service.id, start_date=date(2026, 7, 13), end_date=date(2026, 7, 13), modality="in_person", practitioner_id=practitioner.id, location_id=loc.id, room_id=room.id)
    params.update(overrides)
    return AvailabilityService(session, ctx).list_available_slots(**params)


def add_booking(session, fixture, *, starts_at, status):
    org, loc, room, practitioner, service, patient = fixture
    booking = Booking(organization_id=org.id, patient_id=patient.id, practitioner_id=practitioner.id, practitioner_service_id=service.id, location_id=loc.id, room_id=room.id, modality="in_person", starts_at=starts_at, ends_at=starts_at + timedelta(minutes=30), status=status, service_name_snapshot=service.name, duration_minutes_snapshot=30, practitioner_name_snapshot=practitioner.full_name, modality_snapshot="in_person", location_name_snapshot=loc.name, price_snapshot=Decimal("1.00"), currency_snapshot="COP", total_amount=Decimal("1.00"), address_snapshot=loc.address, room_snapshot=room.name)
    session.add(booking)
    session.flush()
    return booking


def test_generates_slots_from_rules_and_returns_internal_source(session, ctx, availability_fixture):
    slots = list_slots(session, ctx, availability_fixture)
    assert [(s.starts_at.time(), s.ends_at.time()) for s in slots] == [(time(9), time(9, 30)), (time(9, 30), time(10)), (time(10), time(10, 30))]
    assert {s.source for s in slots} == {"internal"}
    assert slots[0].location_id == availability_fixture[1].id
    assert slots[0].room_id == availability_fixture[2].id


def test_respects_practitioner_service_duration(session, ctx, availability_fixture):
    availability_fixture[4].duration_minutes = 45
    assert [(s.starts_at.time(), s.ends_at.time()) for s in list_slots(session, ctx, availability_fixture)] == [(time(9), time(9, 45)), (time(9, 45), time(10, 30))]


def test_filters_by_modality(session, ctx, availability_fixture):
    assert list_slots(session, ctx, availability_fixture, modality="virtual") == []


def test_respects_rule_validity_dates(session, ctx, availability_fixture):
    rule = session.scalar(select(AvailabilityRule))
    rule.valid_from = date(2026, 7, 14)
    assert list_slots(session, ctx, availability_fixture) == []
    rule.valid_from = date(2026, 7, 1)
    rule.valid_to = date(2026, 7, 12)
    assert list_slots(session, ctx, availability_fixture) == []


def test_inactive_exception_does_not_remove_slots(session, ctx, availability_fixture):
    _org, loc, room, practitioner, _service, _patient = availability_fixture
    session.add(AvailabilityException(practitioner_id=practitioner.id, location_id=loc.id, room_id=room.id, starts_at=datetime(2026, 7, 13, 9, 15), ends_at=datetime(2026, 7, 13, 9, 45), exception_type="vacation", status="inactive"))
    session.flush()
    assert len(list_slots(session, ctx, availability_fixture)) == 3


def test_deduplicates_equivalent_slots_and_uses_requested_modality(session, ctx, availability_fixture):
    org, loc, room, practitioner, service, _patient = availability_fixture
    session.add(AvailabilityRule(organization_id=org.id, practitioner_id=practitioner.id, practitioner_service_id=service.id, location_id=loc.id, room_id=room.id, modality="both", weekday=1, start_time=time(9), end_time=time(10, 30), valid_from=date(2026, 7, 1), status="active"))
    session.flush()
    slots = list_slots(session, ctx, availability_fixture)
    assert len(slots) == 3
    assert {slot.modality for slot in slots} == {"in_person"}


def test_filters_by_practitioner_service_location_and_room(session, ctx, availability_fixture):
    with pytest.raises(DomainValidationError, match="practitioner_id"):
        list_slots(session, ctx, availability_fixture, practitioner_id=uuid4())
    assert list_slots(session, ctx, availability_fixture, location_id=uuid4()) == []
    assert list_slots(session, ctx, availability_fixture, room_id=uuid4()) == []


def test_no_rules_returns_empty_list(session, ctx, availability_fixture):
    session.query(AvailabilityRule).delete()
    assert list_slots(session, ctx, availability_fixture) == []


def test_excludes_slots_covered_by_availability_exceptions(session, ctx, availability_fixture):
    _org, loc, room, practitioner, _service, _patient = availability_fixture
    session.add(AvailabilityException(practitioner_id=practitioner.id, location_id=loc.id, room_id=room.id, starts_at=datetime(2026, 7, 13, 9, 15), ends_at=datetime(2026, 7, 13, 9, 45), exception_type="unavailable", status="active"))
    session.flush()
    assert [(s.starts_at.time(), s.ends_at.time()) for s in list_slots(session, ctx, availability_fixture)] == [(time(10), time(10, 30))]


def test_excludes_slots_overlapping_active_bookings(session, ctx, availability_fixture):
    add_booking(session, availability_fixture, starts_at=datetime(2026, 7, 13, 9, 30), status="confirmed")
    assert [(s.starts_at.time(), s.ends_at.time()) for s in list_slots(session, ctx, availability_fixture)] == [(time(9), time(9, 30)), (time(10), time(10, 30))]


def test_terminal_bookings_do_not_block_slots(session, ctx, availability_fixture):
    add_booking(session, availability_fixture, starts_at=datetime(2026, 7, 13, 9, 30), status="cancelled_by_patient")
    assert len(list_slots(session, ctx, availability_fixture)) == 3


def test_rejects_invalid_date_range_or_missing_required_context(session, ctx, availability_fixture):
    with pytest.raises(DomainValidationError):
        list_slots(session, ctx, availability_fixture, start_date=date(2026, 7, 14), end_date=date(2026, 7, 13))
    with pytest.raises(DomainValidationError):
        AvailabilityService(session, None)  # type: ignore[arg-type]
    with pytest.raises(DomainValidationError):
        InternalSchedulingProvider().list_available_slots(session, None, practitioner_service_id=availability_fixture[4].id, start_date=date(2026, 7, 13), end_date=date(2026, 7, 13), modality="in_person")  # type: ignore[arg-type]
    with pytest.raises(DomainValidationError, match="cannot exceed 31 days"):
        list_slots(session, ctx, availability_fixture, start_date=date(2026, 7, 1), end_date=date(2026, 8, 1))
    with pytest.raises(DomainValidationError, match="location_id"):
        list_slots(session, ctx, availability_fixture, location_id=None)


def test_internal_scheduling_provider_treats_rescheduled_as_active_status():
    assert "rescheduled" in InternalSchedulingProvider.ACTIVE_STATUSES


def test_rescheduled_booking_blocks_available_slots(session, ctx, availability_fixture):
    add_booking(session, availability_fixture, starts_at=datetime(2026, 7, 13, 9, 30), status="rescheduled")
    assert [(s.starts_at.time(), s.ends_at.time()) for s in list_slots(session, ctx, availability_fixture)] == [(time(9), time(9, 30)), (time(10), time(10, 30))]


def test_internal_scheduling_provider_can_exclude_same_booking_from_conflict(session, availability_fixture):
    _org, loc, room, practitioner, _service, _patient = availability_fixture
    booking = add_booking(session, availability_fixture, starts_at=datetime(2026, 7, 13, 9, 30), status="confirmed")
    InternalSchedulingProvider().ensure_slot_available(
        session,
        starts_at=booking.starts_at,
        ends_at=booking.ends_at,
        practitioner_id=practitioner.id,
        location_id=loc.id,
        room_id=room.id,
        exclude_booking_id=booking.id,
    )


def test_internal_scheduling_provider_still_rejects_other_active_booking_with_exclusion(session, availability_fixture):
    _org, loc, room, practitioner, _service, _patient = availability_fixture
    booking = add_booking(session, availability_fixture, starts_at=datetime(2026, 7, 13, 9, 30), status="confirmed")
    other_booking = add_booking(session, availability_fixture, starts_at=datetime(2026, 7, 13, 9, 30), status="confirmed_without_payment")
    with pytest.raises(SlotNotAvailable):
        InternalSchedulingProvider().ensure_slot_available(
            session,
            starts_at=booking.starts_at,
            ends_at=booking.ends_at,
            practitioner_id=practitioner.id,
            location_id=loc.id,
            room_id=room.id,
            exclude_booking_id=booking.id,
        )
    assert other_booking.id != booking.id
