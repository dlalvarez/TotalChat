from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.admin.dependencies import get_admin_tenant_context, get_db_session
from app.main import app
from app.models.tenant import Organization, OrganizationPractitioner, Practitioner
from app.tenancy.context import TenantContext

TENANT_TABLES = [Organization.__table__, Practitioner.__table__, OrganizationPractitioner.__table__]


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


def clear_overrides():
    app.dependency_overrides.clear()


def install_overrides(session, tenant_context):
    def override_session():
        yield session
    app.dependency_overrides[get_db_session] = override_session
    app.dependency_overrides[get_admin_tenant_context] = lambda: tenant_context


def create_org(session, name="Clínica Vida", status="active"):
    org = Organization(name=name, organization_type="clinic", status=status)
    session.add(org); session.flush(); return org


def create_practitioner(session, name="Dra. Ana Pérez", status="active"):
    practitioner = Practitioner(full_name=name, status=status)
    session.add(practitioner); session.flush(); return practitioner


def post(client, tenant_context, org, practitioner, role="member", extra=None):
    payload = {"organization_id": str(org.id), "practitioner_id": str(practitioner.id), "role": role}
    if extra:
        payload.update(extra)
    return client.post("/api/admin/organization-practitioners", json=payload, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})


def test_create_list_filter_disable_reactivate_and_edit_role(admin_session, tenant_context):
    org = create_org(admin_session); other_org = create_org(admin_session, "Centro Médico Norte")
    practitioner = create_practitioner(admin_session); other_practitioner = create_practitioner(admin_session, "Dr. Juan Gómez")
    install_overrides(admin_session, tenant_context); client = TestClient(app)
    try:
        created = post(client, tenant_context, org, practitioner)
        post(client, tenant_context, other_org, practitioner, "external")
        post(client, tenant_context, org, other_practitioner, "primary")
        by_org = client.get(f"/api/admin/organization-practitioners?organization_id={org.id}", headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
        by_practitioner = client.get(f"/api/admin/organization-practitioners?practitioner_id={practitioner.id}", headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
        patched = client.patch(f"/api/admin/organizations/{org.id}/practitioners/{practitioner.id}", json={"role": "primary"}, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
        disabled = client.post(f"/api/admin/organizations/{org.id}/practitioners/{practitioner.id}/disable", json={}, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
        inactive = client.get("/api/admin/organization-practitioners?status=inactive", headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
        restored = post(client, tenant_context, org, practitioner, "member")
    finally:
        clear_overrides()
    assert created.status_code == 200
    data = created.json()["data"]
    assert data["organization_name"] == "Clínica Vida" and data["practitioner_name"] == "Dra. Ana Pérez"
    assert "schema_name" not in data
    assert len(by_org.json()["data"]) == 2
    assert len(by_practitioner.json()["data"]) == 2
    assert patched.json()["data"]["role"] == "primary"
    assert disabled.json()["data"]["status"] == "inactive"
    assert inactive.json()["data"][0]["status"] == "inactive"
    assert restored.json()["data"]["status"] == "active"
    assert admin_session.scalars(select(OrganizationPractitioner).where(OrganizationPractitioner.organization_id == org.id, OrganizationPractitioner.practitioner_id == practitioner.id)).all().__len__() == 1


@pytest.mark.parametrize("payload,expected", [({"role": "bad"}, 422), ({"organization_id": str(uuid4())}, 404), ({"practitioner_id": str(uuid4())}, 404), ({"schema_name": "tenant_evil"}, 422)])
def test_rejections(admin_session, tenant_context, payload, expected):
    org = create_org(admin_session); practitioner = create_practitioner(admin_session)
    install_overrides(admin_session, tenant_context)
    try:
        response = post(TestClient(app), tenant_context, org, practitioner, extra=payload)
    finally:
        clear_overrides()
    assert response.status_code == expected


@pytest.mark.parametrize("org_status,practitioner_status", [("inactive", "active"), ("active", "inactive")])
def test_inactive_parent_rejected_for_new_relation(admin_session, tenant_context, org_status, practitioner_status):
    org = create_org(admin_session, status=org_status); practitioner = create_practitioner(admin_session, status=practitioner_status)
    install_overrides(admin_session, tenant_context)
    try:
        response = post(TestClient(app), tenant_context, org, practitioner)
    finally:
        clear_overrides()
    assert response.status_code == 409


def test_existing_relation_remains_visible_when_parent_becomes_inactive(admin_session, tenant_context):
    org = create_org(admin_session); practitioner = create_practitioner(admin_session)
    rel = OrganizationPractitioner(organization=org, practitioner=practitioner, role="member", status="active")
    admin_session.add(rel); admin_session.flush(); org.status = "inactive"; practitioner.status = "inactive"; admin_session.flush()
    install_overrides(admin_session, tenant_context)
    try:
        response = TestClient(app).get("/api/admin/organization-practitioners", headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()
    data = response.json()["data"][0]
    assert data["organization_status"] == "inactive" and data["practitioner_status"] == "inactive"


def test_missing_tenant_header_returns_authentication_required():
    response = TestClient(app).get("/api/admin/organization-practitioners")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"
