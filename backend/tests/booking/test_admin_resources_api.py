from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.admin.dependencies import get_admin_tenant_context, get_db_session
from app.main import app
from app.models.tenant import Location, Organization, Room
from app.tenancy.context import TenantContext

TENANT_TABLES = [Organization.__table__, Location.__table__, Room.__table__]


@pytest.fixture()
def tenant_context():
    return TenantContext(tenant_id=uuid4(), slug="clinica-vida", schema_name="tenant_clinica_vida")


@pytest.fixture()
def admin_resource_session():
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


def post_org_payload(name="Clínica Vida"):
    return {
        "name": name,
        "organization_type": "clinic",
        "legal_name": "Clínica Vida SAS",
        "tax_id": "900123456",
        "email": "admin@example.com",
        "phone": "+573001112233",
    }


def create_org(client, tenant_context, name="Clínica Vida"):
    response = client.post("/api/admin/organizations", json=post_org_payload(name), headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    assert response.status_code == 200
    return response.json()["data"]


def test_create_organization(admin_resource_session, tenant_context):
    install_overrides(admin_resource_session, tenant_context)
    try:
        response = TestClient(app).post("/api/admin/organizations", json=post_org_payload(), headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["name"] == "Clínica Vida"
    assert data["status"] == "active"
    assert UUID(data["id"])
    assert "schema_name" not in data


def test_list_organizations(admin_resource_session, tenant_context):
    install_overrides(admin_resource_session, tenant_context)
    client = TestClient(app)
    try:
        create_org(client, tenant_context, "Zeta")
        create_org(client, tenant_context, "Alpha")
        response = client.get("/api/admin/organizations", headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()

    assert response.status_code == 200
    assert [item["name"] for item in response.json()["data"]] == ["Alpha", "Zeta"]


def test_get_organization_by_id(admin_resource_session, tenant_context):
    install_overrides(admin_resource_session, tenant_context)
    client = TestClient(app)
    try:
        created = create_org(client, tenant_context)
        response = client.get(f"/api/admin/organizations/{created['id']}", headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()

    assert response.status_code == 200
    assert response.json()["data"]["id"] == created["id"]


def test_patch_organization(admin_resource_session, tenant_context):
    install_overrides(admin_resource_session, tenant_context)
    client = TestClient(app)
    try:
        created = create_org(client, tenant_context)
        response = client.patch(f"/api/admin/organizations/{created['id']}", json={"name": "Clínica Actualizada", "email": "new@example.com"}, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()

    assert response.status_code == 200
    assert response.json()["data"]["name"] == "Clínica Actualizada"
    assert response.json()["data"]["email"] == "new@example.com"


def test_disable_organization(admin_resource_session, tenant_context):
    install_overrides(admin_resource_session, tenant_context)
    client = TestClient(app)
    try:
        created = create_org(client, tenant_context)
        response = client.post(f"/api/admin/organizations/{created['id']}/disable", json={}, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "inactive"
    assert admin_resource_session.get(Organization, UUID(created["id"])) is not None


def test_create_location_under_organization(admin_resource_session, tenant_context):
    install_overrides(admin_resource_session, tenant_context)
    client = TestClient(app)
    try:
        org = create_org(client, tenant_context)
        response = client.post("/api/admin/locations", json={"organization_id": org["id"], "name": "Sede Norte", "address": "Calle 123", "city": "Bogotá"}, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["organization_id"] == org["id"]
    assert data["name"] == "Sede Norte"


def test_list_locations(admin_resource_session, tenant_context):
    org = Organization(name="Clínica Vida", organization_type="clinic")
    admin_resource_session.add(org); admin_resource_session.flush()
    admin_resource_session.add_all([Location(organization_id=org.id, name="Zeta"), Location(organization_id=org.id, name="Alpha")]); admin_resource_session.flush()
    install_overrides(admin_resource_session, tenant_context)
    try:
        response = TestClient(app).get("/api/admin/locations", headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()
    assert response.status_code == 200
    assert [item["name"] for item in response.json()["data"]] == ["Alpha", "Zeta"]


def test_create_room_under_location(admin_resource_session, tenant_context):
    org = Organization(name="Clínica Vida", organization_type="clinic")
    loc = Location(organization=org, name="Sede Norte")
    admin_resource_session.add_all([org, loc]); admin_resource_session.flush()
    install_overrides(admin_resource_session, tenant_context)
    try:
        response = TestClient(app).post("/api/admin/rooms", json={"location_id": str(loc.id), "name": "Consultorio 1", "room_type": "consultorio", "capacity": 2}, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()
    assert response.status_code == 200
    assert response.json()["data"]["location_id"] == str(loc.id)
    assert response.json()["data"]["name"] == "Consultorio 1"


def test_list_rooms(admin_resource_session, tenant_context):
    org = Organization(name="Clínica Vida", organization_type="clinic")
    loc = Location(organization=org, name="Sede Norte")
    admin_resource_session.add_all([org, loc]); admin_resource_session.flush()
    admin_resource_session.add_all([Room(location_id=loc.id, name="Zeta"), Room(location_id=loc.id, name="Alpha")]); admin_resource_session.flush()
    install_overrides(admin_resource_session, tenant_context)
    try:
        response = TestClient(app).get("/api/admin/rooms", headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()
    assert response.status_code == 200
    assert [item["name"] for item in response.json()["data"]] == ["Alpha", "Zeta"]


@pytest.mark.parametrize("path,payload", [("/api/admin/locations", {"organization_id": str(uuid4()), "name": "Sede"}), ("/api/admin/rooms", {"location_id": str(uuid4()), "name": "Consultorio"})])
def test_unknown_parent_returns_resource_not_found(admin_resource_session, tenant_context, path, payload):
    install_overrides(admin_resource_session, tenant_context)
    try:
        response = TestClient(app).post(path, json=payload, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_schema_name_in_payload_is_rejected(admin_resource_session, tenant_context):
    install_overrides(admin_resource_session, tenant_context)
    try:
        response = TestClient(app).post("/api/admin/organizations", json={**post_org_payload(), "schema_name": "tenant_evil"}, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_missing_tenant_header_returns_authentication_required():
    response = TestClient(app).post("/api/admin/organizations", json=post_org_payload())
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"
