from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.admin.dependencies import get_admin_tenant_context, get_db_session
from app.main import app
from app.models.tenant import AvailabilityException, AvailabilityRule, Location, Organization, Practitioner, PractitionerService, Room
from app.tenancy.context import TenantContext

TENANT_TABLES = [
    Organization.__table__,
    Location.__table__,
    Room.__table__,
    Practitioner.__table__,
    PractitionerService.__table__,
    AvailabilityRule.__table__,
    AvailabilityException.__table__,
]


@pytest.fixture()
def tenant_context():
    return TenantContext(tenant_id=uuid4(), slug="clinica-vida", schema_name="tenant_clinica_vida")


@pytest.fixture()
def availability_admin_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    for table in TENANT_TABLES:
        table.create(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture()
def seed_data(availability_admin_session):
    org = Organization(name="Clínica Vida", organization_type="clinic")
    practitioner = Practitioner(full_name="Dra. Ana")
    availability_admin_session.add_all([org, practitioner])
    availability_admin_session.flush()
    location = Location(organization_id=org.id, name="Sede Norte")
    service = PractitionerService(organization_id=org.id, practitioner_id=practitioner.id, name="Consulta", duration_minutes=30, requires_payment=True)
    availability_admin_session.add_all([location, service])
    availability_admin_session.flush()
    room = Room(location_id=location.id, name="101")
    availability_admin_session.add(room)
    availability_admin_session.commit()
    return {"org": org, "practitioner": practitioner, "location": location, "room": room, "service": service}


def clear_overrides() -> None:
    app.dependency_overrides.clear()


def install_overrides(session, tenant_context, include_tenant=True):
    def override_session():
        yield session

    app.dependency_overrides[get_db_session] = override_session
    if include_tenant:
        app.dependency_overrides[get_admin_tenant_context] = lambda: tenant_context


def rule_payload(seed_data, **overrides):
    payload = {
        "organization_id": str(seed_data["org"].id),
        "practitioner_id": str(seed_data["practitioner"].id),
        "practitioner_service_id": None,
        "location_id": None,
        "room_id": None,
        "modality": "both",
        "weekday": 1,
        "start_time": "08:00:00",
        "end_time": "12:00:00",
        "valid_from": "2026-07-01",
        "valid_to": None,
        "buffer_minutes": 0,
    }
    payload.update(overrides)
    return payload


def exception_payload(seed_data, **overrides):
    payload = {
        "practitioner_id": str(seed_data["practitioner"].id),
        "location_id": None,
        "room_id": None,
        "starts_at": "2026-07-10T08:00:00",
        "ends_at": "2026-07-10T12:00:00",
        "exception_type": "blocked",
        "reason": "Cierre administrativo",
    }
    payload.update(overrides)
    return payload


def post(path, payload, session, tenant_context, include_tenant=True):
    install_overrides(session, tenant_context, include_tenant=include_tenant)
    try:
        return TestClient(app).post(path, json=payload, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()


def test_create_availability_rule_minimal_payload(availability_admin_session, tenant_context, seed_data):
    response = post("/api/admin/availability-rules", rule_payload(seed_data), availability_admin_session, tenant_context)
    assert response.status_code == 200
    data = response.json()["data"]
    assert UUID(data["id"])
    assert data["organization_id"] == str(seed_data["org"].id)
    assert data["status"] == "active"
    assert "schema_name" not in data


def test_create_availability_rule_with_practitioner_service(availability_admin_session, tenant_context, seed_data):
    response = post("/api/admin/availability-rules", rule_payload(seed_data, practitioner_service_id=str(seed_data["service"].id)), availability_admin_session, tenant_context)
    assert response.status_code == 200
    assert response.json()["data"]["practitioner_service_id"] == str(seed_data["service"].id)


def test_create_availability_rule_in_person_with_location_room(availability_admin_session, tenant_context, seed_data):
    response = post("/api/admin/availability-rules", rule_payload(seed_data, modality="in_person", location_id=str(seed_data["location"].id), room_id=str(seed_data["room"].id)), availability_admin_session, tenant_context)
    assert response.status_code == 200
    assert response.json()["data"]["room_id"] == str(seed_data["room"].id)


@pytest.mark.parametrize("field,message", [("organization_id", "Organization"), ("practitioner_id", "Practitioner"), ("practitioner_service_id", "Practitioner service"), ("location_id", "Location"), ("room_id", "Room")])
def test_create_availability_rule_unknown_references_return_resource_not_found(availability_admin_session, tenant_context, seed_data, field, message):
    payload = rule_payload(seed_data, **{field: str(uuid4())})
    if field == "room_id":
        payload["location_id"] = str(seed_data["location"].id)
    response = post("/api/admin/availability-rules", payload, availability_admin_session, tenant_context)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"
    assert message in response.json()["error"]["message"]


@pytest.mark.parametrize("overrides", [{"schema_name": "tenant_x"}, {"weekday": 8}, {"start_time": "12:00:00", "end_time": "12:00:00"}, {"valid_from": "2026-07-02", "valid_to": "2026-07-01"}, {"buffer_minutes": -1}])
def test_create_availability_rule_validation_errors(availability_admin_session, tenant_context, seed_data, overrides):
    response = post("/api/admin/availability-rules", rule_payload(seed_data, **overrides), availability_admin_session, tenant_context)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_create_availability_exception_success(availability_admin_session, tenant_context, seed_data):
    response = post("/api/admin/availability-exceptions", exception_payload(seed_data), availability_admin_session, tenant_context)
    assert response.status_code == 200
    data = response.json()["data"]
    assert UUID(data["id"])
    assert data["exception_type"] == "blocked"
    assert data["status"] == "active"
    assert "schema_name" not in data


@pytest.mark.parametrize("field,message", [("practitioner_id", "Practitioner"), ("location_id", "Location"), ("room_id", "Room")])
def test_create_availability_exception_unknown_references_return_resource_not_found(availability_admin_session, tenant_context, seed_data, field, message):
    payload = exception_payload(seed_data, **{field: str(uuid4())})
    if field == "room_id":
        payload["location_id"] = str(seed_data["location"].id)
    response = post("/api/admin/availability-exceptions", payload, availability_admin_session, tenant_context)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"
    assert message in response.json()["error"]["message"]


@pytest.mark.parametrize("overrides", [{"schema_name": "tenant_x"}, {"starts_at": "2026-07-10T12:00:00", "ends_at": "2026-07-10T12:00:00"}])
def test_create_availability_exception_validation_errors(availability_admin_session, tenant_context, seed_data, overrides):
    response = post("/api/admin/availability-exceptions", exception_payload(seed_data, **overrides), availability_admin_session, tenant_context)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.parametrize("path,payload_factory", [("/api/admin/availability-rules", rule_payload), ("/api/admin/availability-exceptions", exception_payload)])
def test_missing_tenant_header_returns_authentication_required_for_availability_endpoints(availability_admin_session, tenant_context, seed_data, path, payload_factory):
    install_overrides(availability_admin_session, tenant_context, include_tenant=False)
    try:
        response = TestClient(app).post(path, json=payload_factory(seed_data))
    finally:
        clear_overrides()
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"
