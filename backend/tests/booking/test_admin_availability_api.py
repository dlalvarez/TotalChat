from datetime import date, time
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.admin.availability import get_scheduling_provider
from app.api.admin.dependencies import get_admin_tenant_context, get_db_session
from app.auth.jwt import create_access_token
from app.models.public import Tenant, User
from app.main import app
from app.models.tenant import AvailabilityException, AvailabilityRule, Booking, Location, Organization, Patient, Practitioner, PractitionerService, Room, ServiceModality
from app.services.availability import AvailableSlot
from app.tenancy.context import TenantContext

TENANT_TABLES = [Organization.__table__, Location.__table__, Room.__table__, Practitioner.__table__, PractitionerService.__table__, ServiceModality.__table__, Patient.__table__, AvailabilityRule.__table__, AvailabilityException.__table__, Booking.__table__]


@pytest.fixture()
def tenant_context():
    return TenantContext(tenant_id=uuid4(), slug="clinica-vida", schema_name="tenant_clinica_vida")


@pytest.fixture()
def session_with_availability():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    for table in TENANT_TABLES:
        table.create(engine)
    with Session(engine) as session:
        org = Organization(name="Clínica Vida", organization_type="clinic")
        loc = Location(organization=org, name="Sede Norte", address="Calle 123")
        room = Room(location=loc, name="Consultorio 301")
        practitioner = Practitioner(full_name="Dra. Ana Pérez", status="active")
        service = PractitionerService(organization=org, practitioner=practitioner, name="Consulta", duration_minutes=30, status="active")
        patient = Patient(full_name="Paciente Uno")
        session.add_all([org, loc, room, practitioner, service, patient])
        session.flush()
        session.add(ServiceModality(practitioner_service_id=service.id, modality="in_person", location_id=loc.id, room_id=room.id, status="active"))
        session.add(AvailabilityRule(organization_id=org.id, practitioner_id=practitioner.id, practitioner_service_id=None, location_id=loc.id, room_id=room.id, modality="in_person", weekday=1, start_time=time(9), end_time=time(10), valid_from=date(2026, 7, 1), status="active"))
        session.flush()
        yield session, loc, room, practitioner, service


def clear_overrides() -> None:
    app.dependency_overrides.clear()


def test_admin_availability_slots_returns_data_wrapper(session_with_availability, tenant_context):
    session, loc, room, practitioner, service = session_with_availability

    def override_session():
        yield session

    app.dependency_overrides[get_db_session] = override_session
    app.dependency_overrides[get_admin_tenant_context] = lambda: tenant_context
    try:
        response = TestClient(app).get(
            "/api/admin/availability/slots",
            params={
                "practitioner_service_id": str(service.id),
                "practitioner_id": str(practitioner.id),
                "modality": "in_person",
                "date_from": "2026-07-13",
                "date_to": "2026-07-13",
                "location_id": str(loc.id),
                "room_id": str(room.id),
            },
            headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)},
        )
    finally:
        clear_overrides()

    assert response.status_code == 200
    body = response.json()
    assert list(body) == ["data"]
    assert len(body["data"]) == 2
    assert body["data"][0]["source"] == "internal"
    assert body["data"][0]["practitioner_id"] == str(practitioner.id)
    assert body["data"][0]["location_id"] == str(loc.id)
    assert body["data"][0]["room_id"] == str(room.id)
    assert "schema_name" not in body["data"][0]


def test_missing_admin_tenant_header_returns_error():
    response = TestClient(app).get(
        "/api/admin/availability/slots",
        params={"practitioner_service_id": str(uuid4()), "modality": "in_person", "date_from": "2026-07-13", "date_to": "2026-07-13"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


@pytest.mark.parametrize("tenant_status", [None, "inactive"])
def test_unknown_or_inactive_tenant_returns_tenant_not_found(tenant_status, monkeypatch):
    monkeypatch.setenv("TOTALCHAT_JWT_SECRET", "test-secret")
    from app.core.config import get_settings
    get_settings.cache_clear()
    user_id = uuid4()
    selected_tenant_id = uuid4()
    token, _expires_in = create_access_token(user_id=user_id, email="admin@example.com")

    class FakeSession:
        def get(self, model, record_id):
            if model is User:
                return SimpleNamespace(id=record_id, email="admin@example.com", status="active")
            if model is Tenant:
                if tenant_status is None:
                    return None
                return SimpleNamespace(id=record_id, slug="inactive", schema_name="tenant_inactive", status=tenant_status)
            return None

    def override_session():
        yield FakeSession()

    app.dependency_overrides[get_db_session] = override_session
    try:
        response = TestClient(app).get(
            "/api/admin/availability/slots",
            params={"practitioner_service_id": str(uuid4()), "modality": "in_person", "date_from": "2026-07-13", "date_to": "2026-07-13"},
            headers={"Authorization": f"Bearer {token}", "X-TotalChat-Tenant-Id": str(selected_tenant_id)},
        )
    finally:
        clear_overrides()
        get_settings.cache_clear()

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "TENANT_NOT_FOUND"


def test_invalid_date_range_maps_to_validation_error(session_with_availability, tenant_context):
    session, _loc, _room, _practitioner, service = session_with_availability

    def override_session():
        yield session

    app.dependency_overrides[get_db_session] = override_session
    app.dependency_overrides[get_admin_tenant_context] = lambda: tenant_context
    try:
        response = TestClient(app).get(
            "/api/admin/availability/slots",
            params={"practitioner_service_id": str(service.id), "modality": "in_person", "date_from": "2026-07-14", "date_to": "2026-07-13"},
            headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)},
        )
    finally:
        clear_overrides()

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_endpoint_delegates_slot_lookup_to_scheduling_provider(tenant_context):
    captured = {}
    practitioner_service_id = uuid4()
    practitioner_id = uuid4()
    location_id = uuid4()
    room_id = uuid4()

    class RecordingProvider:
        def list_available_slots(self, session, tenant_context_arg, **kwargs):
            captured["session"] = session
            captured["tenant_context"] = tenant_context_arg
            captured["kwargs"] = kwargs
            return [AvailableSlot(starts_at=__import__("datetime").datetime(2026, 7, 13, 9), ends_at=__import__("datetime").datetime(2026, 7, 13, 9, 30), practitioner_id=practitioner_id, location_id=location_id, room_id=room_id, modality="in_person")]

    sentinel_session = object()

    def override_session():
        yield sentinel_session

    app.dependency_overrides[get_db_session] = override_session
    app.dependency_overrides[get_admin_tenant_context] = lambda: tenant_context
    app.dependency_overrides[get_scheduling_provider] = lambda: RecordingProvider()
    try:
        response = TestClient(app).get(
            "/api/admin/availability/slots",
            params={
                "practitioner_service_id": str(practitioner_service_id),
                "practitioner_id": str(practitioner_id),
                "modality": "in_person",
                "date_from": "2026-07-13",
                "date_to": "2026-07-13",
                "payer_plan_id": str(uuid4()),
                "location_id": str(location_id),
                "room_id": str(room_id),
            },
            headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)},
        )
    finally:
        clear_overrides()

    assert response.status_code == 200
    assert captured["session"] is sentinel_session
    assert captured["tenant_context"] == tenant_context
    assert captured["kwargs"]["practitioner_service_id"] == practitioner_service_id
    assert captured["kwargs"]["start_date"] == date(2026, 7, 13)
    assert response.json()["data"][0]["source"] == "internal"
