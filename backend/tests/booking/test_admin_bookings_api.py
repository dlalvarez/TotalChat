from datetime import date, datetime, time
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.admin.bookings import get_booking_scheduling_provider
from app.api.admin.dependencies import get_admin_tenant_context, get_db_session
from app.main import app
from app.models.tenant import (
    AvailabilityRule,
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
)
from app.tenancy.context import TenantContext

TENANT_TABLES = [
    Organization.__table__, Location.__table__, Room.__table__, Practitioner.__table__, PractitionerService.__table__,
    ServiceModality.__table__, PayerType.__table__, Payer.__table__, PayerPlan.__table__, PractitionerServicePrice.__table__,
    Patient.__table__, AvailabilityRule.__table__, Booking.__table__,
]


@pytest.fixture()
def tenant_context():
    return TenantContext(tenant_id=uuid4(), slug="clinica-vida", schema_name="tenant_clinica_vida")


@pytest.fixture()
def booking_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    for table in TENANT_TABLES:
        table.create(engine)
    with Session(engine) as session:
        org = Organization(name="Clínica Vida", organization_type="clinic")
        loc = Location(organization=org, name="Sede Norte", address="Calle 123")
        room = Room(location=loc, name="Consultorio 301")
        practitioner = Practitioner(full_name="Dra. Ana Pérez", status="active")
        service = PractitionerService(organization=org, practitioner=practitioner, name="Consulta psicológica", duration_minutes=50, status="active")
        payer_type = PayerType(code="particular", name="Particular", status="active")
        payer = Payer(payer_type=payer_type, name="Particular", status="active")
        plan = PayerPlan(payer=payer, name="Tarifa particular", status="active")
        price = PractitionerServicePrice(practitioner_service=service, payer_plan=plan, price=Decimal("100000.00"), currency="COP", valid_from=date(2026, 1, 1), status="active")
        patient = Patient(full_name="Paciente Existente", phone="+573009990000", email="existente@example.com")
        session.add_all([org, loc, room, practitioner, service, payer_type, payer, plan, price, patient])
        session.flush()
        session.add(ServiceModality(practitioner_service_id=service.id, modality="in_person", location_id=loc.id, room_id=room.id, status="active"))
        session.add(AvailabilityRule(organization_id=org.id, practitioner_id=practitioner.id, practitioner_service_id=None, location_id=loc.id, room_id=room.id, modality="in_person", weekday=5, start_time=time(9), end_time=time(11), valid_from=date(2026, 7, 1), status="active"))
        session.flush()
        yield session, loc, room, practitioner, service, plan, price, patient


def clear_overrides() -> None:
    app.dependency_overrides.clear()


def install_overrides(session, tenant_context):
    def override_session():
        yield session

    app.dependency_overrides[get_db_session] = override_session
    app.dependency_overrides[get_admin_tenant_context] = lambda: tenant_context


def payload(loc, room, service, plan, *, patient=None, starts_at="2026-07-10T09:00:00-05:00"):
    return {
        "patient": patient or {"id": None, "full_name": "Juan Pérez", "phone": "+573001112233", "email": None},
        "practitioner_service_id": str(service.id),
        "payer_plan_id": str(plan.id),
        "modality": "in_person",
        "starts_at": starts_at,
        "location_id": str(loc.id),
        "room_id": str(room.id),
        "created_channel": "admin",
    }


def test_admin_bookings_create_tentative_booking_with_minimal_patient(booking_session, tenant_context):
    session, loc, room, _practitioner, service, plan, _price, _existing_patient = booking_session
    install_overrides(session, tenant_context)
    try:
        response = TestClient(app).post("/api/admin/bookings", json=payload(loc, room, service, plan), headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()

    assert response.status_code == 200
    body = response.json()
    assert list(body) == ["data"]
    data = body["data"]
    assert data["status"] == "tentative"
    assert data["payment_status"] == "pending"
    assert data["service_name_snapshot"] == "Consulta psicológica"
    assert data["payer_plan_name_snapshot"] == "Tarifa particular"
    assert data["price_snapshot"] == 100000
    assert data["currency_snapshot"] == "COP"
    assert data["total_amount"] == 100000
    assert "schema_name" not in data
    patient = session.get(Patient, UUID(data["patient_id"]))
    assert patient.full_name == "Juan Pérez"
    assert patient.profile_status == "minimal"
    assert patient.created_from_channel == "admin"


def test_admin_bookings_uses_existing_patient_when_id_is_provided(booking_session, tenant_context):
    session, loc, room, _practitioner, service, plan, _price, existing_patient = booking_session
    install_overrides(session, tenant_context)
    try:
        response = TestClient(app).post(
            "/api/admin/bookings",
            json=payload(loc, room, service, plan, patient={"id": str(existing_patient.id), "full_name": None, "phone": None, "email": None}, starts_at="2026-07-10T10:00:00-05:00"),
            headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)},
        )
    finally:
        clear_overrides()

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["patient_id"] == str(existing_patient.id)
    assert session.scalar(select(Patient).where(Patient.full_name == "Juan Pérez")) is None


def test_admin_bookings_missing_tenant_header_returns_authentication_required():
    response = TestClient(app).post("/api/admin/bookings", json={"patient": {"full_name": "Juan Pérez"}, "practitioner_service_id": str(uuid4()), "payer_plan_id": str(uuid4()), "modality": "in_person", "starts_at": "2026-07-10T09:00:00-05:00", "created_channel": "admin"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


def test_admin_bookings_slot_conflict_maps_to_slot_not_available(booking_session, tenant_context):
    session, loc, room, practitioner, service, plan, _price, existing_patient = booking_session
    session.add(Booking(
        organization_id=service.organization_id, patient_id=existing_patient.id, practitioner_id=practitioner.id,
        practitioner_service_id=service.id, payer_plan_id=plan.id, location_id=loc.id, room_id=room.id, modality="in_person",
        starts_at=datetime(2026, 7, 10, 9, 0), ends_at=datetime(2026, 7, 10, 9, 50), status="tentative",
        service_name_snapshot=service.name, duration_minutes_snapshot=service.duration_minutes, practitioner_name_snapshot=practitioner.full_name,
        modality_snapshot="in_person", payer_plan_name_snapshot=plan.name, price_snapshot=Decimal("100000.00"), currency_snapshot="COP", total_amount=Decimal("100000.00"),
    ))
    session.flush()
    install_overrides(session, tenant_context)
    try:
        response = TestClient(app).post("/api/admin/bookings", json=payload(loc, room, service, plan), headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SLOT_NOT_AVAILABLE"


def test_admin_bookings_missing_price_maps_to_resource_not_found(booking_session, tenant_context):
    session, loc, room, _practitioner, service, plan, price, _existing_patient = booking_session
    price.status = "inactive"
    session.flush()
    install_overrides(session, tenant_context)
    try:
        response = TestClient(app).post("/api/admin/bookings", json=payload(loc, room, service, plan), headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_admin_bookings_endpoint_delegates_to_booking_service_scheduling_provider(booking_session, tenant_context):
    session, loc, room, _practitioner, service, plan, _price, _existing_patient = booking_session
    captured = {"called": False}

    class RecordingProvider:
        def list_available_slots(self, session, tenant_context, **kwargs):
            return []

        def ensure_slot_available(self, session, **kwargs):
            captured["called"] = True
            captured["session"] = session
            captured["kwargs"] = kwargs

    install_overrides(session, tenant_context)
    app.dependency_overrides[get_booking_scheduling_provider] = lambda: RecordingProvider()
    try:
        response = TestClient(app).post("/api/admin/bookings", json=payload(loc, room, service, plan), headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()

    assert response.status_code == 200
    assert captured["called"] is True
    assert captured["session"] is session
    assert captured["kwargs"]["location_id"] == loc.id
