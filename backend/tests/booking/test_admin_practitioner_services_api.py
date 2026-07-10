from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.admin.dependencies import get_admin_tenant_context, get_db_session
from app.main import app
from app.models.tenant import Location, Organization, OrganizationPractitioner, Practitioner, PractitionerService, Room, ServiceModality
from app.tenancy.context import TenantContext

TENANT_TABLES = [Organization.__table__, Practitioner.__table__, OrganizationPractitioner.__table__, Location.__table__, Room.__table__, PractitionerService.__table__, ServiceModality.__table__]


@pytest.fixture()
def tenant_context():
    return TenantContext(tenant_id=uuid4(), slug="clinica-vida", schema_name="tenant_clinica_vida")


@pytest.fixture()
def admin_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    for table in TENANT_TABLES:
        table.create(engine)
    with Session(engine) as session:
        yield session


def clear_overrides() -> None:
    app.dependency_overrides.clear()


def install_overrides(session, tenant_context):
    def override_session():
        yield session

    app.dependency_overrides[get_db_session] = override_session
    app.dependency_overrides[get_admin_tenant_context] = lambda: tenant_context


@pytest.fixture()
def base_data(admin_session):
    org = Organization(name="Clínica Vida", organization_type="clinic")
    practitioner = Practitioner(full_name="Dra. Ana Pérez")
    loc = Location(organization=org, name="Sede Norte")
    other_loc = Location(organization=org, name="Sede Sur")
    room = Room(location=loc, name="Consultorio 1")
    other_room = Room(location=other_loc, name="Consultorio 2")
    admin_session.add_all([org, practitioner, loc, other_loc, room, other_room])
    admin_session.flush()
    admin_session.add(OrganizationPractitioner(organization_id=org.id, practitioner_id=practitioner.id))
    admin_session.flush()
    return org, practitioner, loc, room, other_loc, other_room


def service_payload(org, practitioner, name="Terapia cognitivo conductual", duration=60):
    return {
        "organization_id": str(org.id),
        "practitioner_id": str(practitioner.id),
        "name": name,
        "description": "Sesión terapéutica individual de 60 minutos.",
        "duration_minutes": duration,
        "requires_payment": True,
    }


def create_service(client, tenant_context, org, practitioner, name="Terapia cognitivo conductual"):
    response = client.post("/api/admin/practitioner-services", json=service_payload(org, practitioner, name), headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    assert response.status_code == 200
    return response.json()["data"]


def test_create_practitioner_service_successfully(admin_session, tenant_context, base_data):
    org, practitioner, *_ = base_data
    install_overrides(admin_session, tenant_context)
    try:
        response = TestClient(app).post("/api/admin/practitioner-services", json=service_payload(org, practitioner), headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()
    assert response.status_code == 200
    data = response.json()["data"]
    assert UUID(data["id"])
    assert data["organization_id"] == str(org.id)
    assert data["practitioner_id"] == str(practitioner.id)
    assert data["duration_minutes"] == 60
    assert data["status"] == "active"
    assert "schema_name" not in data


def test_create_practitioner_service_returns_readable_names_without_lazy_loading_error(admin_session, tenant_context, base_data):
    org, practitioner, *_ = base_data
    install_overrides(admin_session, tenant_context)
    try:
        response = TestClient(app).post(
            "/api/admin/practitioner-services",
            json=service_payload(org, practitioner, "Consulta pediátrica"),
            headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)},
        )
    finally:
        clear_overrides()

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["organization_name"] == "Clínica Vida"
    assert data["practitioner_name"] == "Dra. Ana Pérez"
    assert data["organization_practitioner_status"] == "active"


def test_list_practitioner_services_with_deterministic_ordering(admin_session, tenant_context, base_data):
    org, practitioner, *_ = base_data
    install_overrides(admin_session, tenant_context)
    client = TestClient(app)
    try:
        create_service(client, tenant_context, org, practitioner, "Zeta")
        create_service(client, tenant_context, org, practitioner, "Alpha")
        response = client.get("/api/admin/practitioner-services", headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()
    assert response.status_code == 200
    assert [item["name"] for item in response.json()["data"]] == ["Alpha", "Zeta"]


def test_create_practitioner_service_rejects_schema_name(admin_session, tenant_context, base_data):
    org, practitioner, *_ = base_data
    install_overrides(admin_session, tenant_context)
    try:
        response = TestClient(app).post("/api/admin/practitioner-services", json={**service_payload(org, practitioner), "schema_name": "tenant_evil"}, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.parametrize("field,message", [("organization_id", "Organization"), ("practitioner_id", "Practitioner")])
def test_create_practitioner_service_unknown_parent_returns_resource_not_found(admin_session, tenant_context, base_data, field, message):
    org, practitioner, *_ = base_data
    payload = service_payload(org, practitioner)
    payload[field] = str(uuid4())
    install_overrides(admin_session, tenant_context)
    try:
        response = TestClient(app).post("/api/admin/practitioner-services", json=payload, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"
    assert message in response.json()["error"]["message"]


def test_create_practitioner_service_non_positive_duration_returns_validation_error(admin_session, tenant_context, base_data):
    org, practitioner, *_ = base_data
    install_overrides(admin_session, tenant_context)
    try:
        response = TestClient(app).post("/api/admin/practitioner-services", json=service_payload(org, practitioner, duration=0), headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"



def test_patch_practitioner_service_returns_readable_names_without_lazy_loading_error(admin_session, tenant_context, base_data):
    org, practitioner, *_ = base_data
    install_overrides(admin_session, tenant_context)
    client = TestClient(app)
    try:
        service = create_service(client, tenant_context, org, practitioner, "Consulta pediátrica")
        response = client.patch(
            f"/api/admin/practitioner-services/{service['id']}",
            json={"description": "Nueva descripción"},
            headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)},
        )
    finally:
        clear_overrides()

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["organization_name"] == "Clínica Vida"
    assert data["practitioner_name"] == "Dra. Ana Pérez"
    assert data["organization_practitioner_status"] == "active"
    assert data["description"] == "Nueva descripción"


def test_disable_practitioner_service_returns_readable_names_without_lazy_loading_error(admin_session, tenant_context, base_data):
    org, practitioner, *_ = base_data
    install_overrides(admin_session, tenant_context)
    client = TestClient(app)
    try:
        service = create_service(client, tenant_context, org, practitioner, "Consulta pediátrica")
        response = client.post(
            f"/api/admin/practitioner-services/{service['id']}/disable",
            headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)},
        )
    finally:
        clear_overrides()

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["organization_name"] == "Clínica Vida"
    assert data["practitioner_name"] == "Dra. Ana Pérez"
    assert data["organization_practitioner_status"] == "active"
    assert data["status"] == "inactive"


def test_get_patch_disable_and_reactivate_practitioner_service(admin_session, tenant_context, base_data):
    org, practitioner, *_ = base_data
    install_overrides(admin_session, tenant_context)
    client = TestClient(app)
    try:
        service = create_service(client, tenant_context, org, practitioner, "Consulta pediátrica")
        get_response = client.get(f"/api/admin/practitioner-services/{service['id']}", headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
        patch_response = client.patch(f"/api/admin/practitioner-services/{service['id']}", json={"name": "Consulta pediátrica integral", "description": "Control", "duration_minutes": 30, "requires_payment": False}, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
        disable_response = client.post(f"/api/admin/practitioner-services/{service['id']}/disable", headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
        reactivate_response = client.patch(f"/api/admin/practitioner-services/{service['id']}", json={"status": "active"}, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()
    assert get_response.status_code == 200
    assert get_response.json()["data"]["organization_name"] == "Clínica Vida"
    assert get_response.json()["data"]["practitioner_name"] == "Dra. Ana Pérez"
    assert get_response.json()["data"]["organization_practitioner_status"] == "active"
    assert patch_response.status_code == 200
    assert patch_response.json()["data"]["duration_minutes"] == 30
    assert patch_response.json()["data"]["requires_payment"] is False
    assert disable_response.status_code == 200
    assert disable_response.json()["data"]["status"] == "inactive"
    assert reactivate_response.status_code == 200
    assert reactivate_response.json()["data"]["status"] == "active"


def test_practitioner_service_rejects_inactive_or_missing_relationship(admin_session, tenant_context, base_data):
    org, practitioner, *_ = base_data
    association = admin_session.get(OrganizationPractitioner, {"organization_id": org.id, "practitioner_id": practitioner.id})
    association.status = "inactive"
    admin_session.flush()
    install_overrides(admin_session, tenant_context)
    try:
        response = TestClient(app).post("/api/admin/practitioner-services", json=service_payload(org, practitioner), headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "BUSINESS_RULE_VIOLATION"


def test_practitioner_service_rejects_duplicate_normalized_name(admin_session, tenant_context, base_data):
    org, practitioner, *_ = base_data
    install_overrides(admin_session, tenant_context)
    client = TestClient(app)
    try:
        create_service(client, tenant_context, org, practitioner, "Consulta pediátrica")
        response = client.post("/api/admin/practitioner-services", json=service_payload(org, practitioner, "  CONSULTA   PEDIÁTRICA  "), headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CONFLICT"


def test_practitioner_service_history_remains_listed_with_inactive_parents(admin_session, tenant_context, base_data):
    org, practitioner, *_ = base_data
    service = PractitionerService(organization_id=org.id, practitioner_id=practitioner.id, name="Consulta histórica", duration_minutes=30)
    admin_session.add(service)
    admin_session.flush()
    org.status = "inactive"
    practitioner.status = "inactive"
    admin_session.get(OrganizationPractitioner, {"organization_id": org.id, "practitioner_id": practitioner.id}).status = "inactive"
    admin_session.flush()
    install_overrides(admin_session, tenant_context)
    try:
        response = TestClient(app).get("/api/admin/practitioner-services", headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()
    assert response.status_code == 200
    data = response.json()["data"][0]
    assert data["organization_status"] == "inactive"
    assert data["practitioner_status"] == "inactive"
    assert data["organization_practitioner_status"] == "inactive"

def test_create_in_person_modality_successfully(admin_session, tenant_context, base_data):
    org, practitioner, loc, room, *_ = base_data
    install_overrides(admin_session, tenant_context)
    client = TestClient(app)
    try:
        service = create_service(client, tenant_context, org, practitioner)
        response = client.post(f"/api/admin/practitioner-services/{service['id']}/modalities", json={"modality": "in_person", "location_id": str(loc.id), "room_id": str(room.id)}, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["practitioner_service_id"] == service["id"]
    assert data["modality"] == "in_person"
    assert data["location_id"] == str(loc.id)
    assert data["room_id"] == str(room.id)
    assert "schema_name" not in data


def test_create_virtual_modality_successfully(admin_session, tenant_context, base_data):
    org, practitioner, *_ = base_data
    install_overrides(admin_session, tenant_context)
    client = TestClient(app)
    try:
        service = create_service(client, tenant_context, org, practitioner)
        response = client.post(f"/api/admin/practitioner-services/{service['id']}/modalities", json={"modality": "virtual", "location_id": None, "room_id": None}, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["modality"] == "virtual"
    assert data["location_id"] is None
    assert data["room_id"] is None


def test_create_modality_rejects_schema_name(admin_session, tenant_context, base_data):
    org, practitioner, *_ = base_data
    install_overrides(admin_session, tenant_context)
    client = TestClient(app)
    try:
        service = create_service(client, tenant_context, org, practitioner)
        response = client.post(f"/api/admin/practitioner-services/{service['id']}/modalities", json={"modality": "virtual", "schema_name": "tenant_evil"}, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_create_modality_for_unknown_service_returns_resource_not_found(admin_session, tenant_context):
    install_overrides(admin_session, tenant_context)
    try:
        response = TestClient(app).post(f"/api/admin/practitioner-services/{uuid4()}/modalities", json={"modality": "virtual"}, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_in_person_modality_requires_location_id_and_room_id(admin_session, tenant_context, base_data):
    org, practitioner, *_ = base_data
    install_overrides(admin_session, tenant_context)
    client = TestClient(app)
    try:
        service = create_service(client, tenant_context, org, practitioner)
        response = client.post(f"/api/admin/practitioner-services/{service['id']}/modalities", json={"modality": "in_person"}, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.parametrize("payload", [{"location_id": str(uuid4()), "room_id": None}, {"location_id": None, "room_id": str(uuid4())}])
def test_in_person_modality_unknown_location_or_room_returns_resource_not_found(admin_session, tenant_context, base_data, payload):
    org, practitioner, loc, room, *_ = base_data
    if payload["location_id"] is None:
        payload["location_id"] = str(loc.id)
    if payload["room_id"] is None:
        payload["room_id"] = str(room.id)
    install_overrides(admin_session, tenant_context)
    client = TestClient(app)
    try:
        service = create_service(client, tenant_context, org, practitioner)
        response = client.post(f"/api/admin/practitioner-services/{service['id']}/modalities", json={"modality": "in_person", **payload}, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_in_person_modality_rejects_room_from_another_location(admin_session, tenant_context, base_data):
    org, practitioner, loc, _room, _other_loc, other_room = base_data
    install_overrides(admin_session, tenant_context)
    client = TestClient(app)
    try:
        service = create_service(client, tenant_context, org, practitioner)
        response = client.post(f"/api/admin/practitioner-services/{service['id']}/modalities", json={"modality": "in_person", "location_id": str(loc.id), "room_id": str(other_room.id)}, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "BUSINESS_RULE_VIOLATION"


def test_virtual_modality_rejects_non_null_location_or_room(admin_session, tenant_context, base_data):
    org, practitioner, loc, room, *_ = base_data
    install_overrides(admin_session, tenant_context)
    client = TestClient(app)
    try:
        service = create_service(client, tenant_context, org, practitioner)
        response = client.post(f"/api/admin/practitioner-services/{service['id']}/modalities", json={"modality": "virtual", "location_id": str(loc.id), "room_id": str(room.id)}, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "BUSINESS_RULE_VIOLATION"


@pytest.mark.parametrize("path,json", [("/api/admin/practitioner-services", {"organization_id": str(uuid4()), "practitioner_id": str(uuid4()), "name": "Consulta", "duration_minutes": 30}), (f"/api/admin/practitioner-services/{uuid4()}/modalities", {"modality": "virtual"})])
def test_missing_tenant_header_returns_authentication_required(path, json):
    response = TestClient(app).post(path, json=json)
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"
