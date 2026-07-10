from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.admin.dependencies import get_admin_tenant_context, get_db_session
from app.main import app
from app.models.tenant import Practitioner, PractitionerSpecialty, Specialty
from app.tenancy.context import TenantContext

TENANT_TABLES = [Practitioner.__table__, Specialty.__table__, PractitionerSpecialty.__table__]


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


def practitioner_payload(name="Ana Gómez"):
    return {
        "full_name": name,
        "professional_type": "psychologist",
        "professional_license": "TP-12345",
        "email": "ana@example.com",
        "phone": "+573001112233",
    }


def specialty_payload(name="Psicología"):
    return {"name": name, "description": "Servicios de psicología clínica y terapias."}


def create_practitioner(client, tenant_context, name="Ana Gómez"):
    response = client.post("/api/admin/practitioners", json=practitioner_payload(name), headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    assert response.status_code == 200
    return response.json()["data"]


def create_specialty(client, tenant_context, name="Psicología"):
    response = client.post("/api/admin/specialties", json=specialty_payload(name), headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    assert response.status_code == 200
    return response.json()["data"]


def test_create_practitioner(admin_session, tenant_context):
    install_overrides(admin_session, tenant_context)
    try:
        response = TestClient(app).post("/api/admin/practitioners", json=practitioner_payload(), headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["full_name"] == "Ana Gómez"
    assert data["status"] == "active"
    assert UUID(data["id"])
    assert "schema_name" not in data


def test_list_practitioners_with_deterministic_ordering(admin_session, tenant_context):
    install_overrides(admin_session, tenant_context)
    client = TestClient(app)
    try:
        create_practitioner(client, tenant_context, "Zeta")
        create_practitioner(client, tenant_context, "Alpha")
        response = client.get("/api/admin/practitioners", headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()
    assert response.status_code == 200
    assert [item["full_name"] for item in response.json()["data"]] == ["Alpha", "Zeta"]


def test_patch_practitioner(admin_session, tenant_context):
    install_overrides(admin_session, tenant_context)
    client = TestClient(app)
    try:
        created = create_practitioner(client, tenant_context)
        response = client.patch(f"/api/admin/practitioners/{created['id']}", json={"full_name": "Ana Actualizada", "status": "inactive"}, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()
    assert response.status_code == 200
    assert response.json()["data"]["full_name"] == "Ana Actualizada"
    assert response.json()["data"]["status"] == "inactive"


def test_unknown_practitioner_patch_returns_resource_not_found(admin_session, tenant_context):
    install_overrides(admin_session, tenant_context)
    try:
        response = TestClient(app).patch(f"/api/admin/practitioners/{uuid4()}", json={"status": "inactive"}, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_practitioner_create_rejects_schema_name(admin_session, tenant_context):
    install_overrides(admin_session, tenant_context)
    try:
        response = TestClient(app).post("/api/admin/practitioners", json={**practitioner_payload(), "schema_name": "tenant_evil"}, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_create_specialty(admin_session, tenant_context):
    install_overrides(admin_session, tenant_context)
    try:
        response = TestClient(app).post("/api/admin/specialties", json=specialty_payload(), headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["name"] == "Psicología"
    assert data["status"] == "active"
    assert "schema_name" not in data


def test_list_specialties_with_deterministic_ordering(admin_session, tenant_context):
    install_overrides(admin_session, tenant_context)
    client = TestClient(app)
    try:
        create_specialty(client, tenant_context, "Zeta")
        create_specialty(client, tenant_context, "Alpha")
        response = client.get("/api/admin/specialties", headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()
    assert response.status_code == 200
    assert [item["name"] for item in response.json()["data"]] == ["Alpha", "Zeta"]


def test_specialty_create_rejects_schema_name(admin_session, tenant_context):
    install_overrides(admin_session, tenant_context)
    try:
        response = TestClient(app).post("/api/admin/specialties", json={**specialty_payload(), "schema_name": "tenant_evil"}, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_assign_specialty_to_practitioner(admin_session, tenant_context):
    install_overrides(admin_session, tenant_context)
    client = TestClient(app)
    try:
        practitioner = create_practitioner(client, tenant_context)
        specialty = create_specialty(client, tenant_context)
        response = client.post(f"/api/admin/practitioners/{practitioner['id']}/specialties", json={"specialty_id": specialty["id"]}, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["practitioner_id"] == practitioner["id"]
    assert data["specialty_id"] == specialty["id"]
    assert data["specialty_name"] == "Psicología"
    assert data["status"] == "active"


def test_assign_specialty_to_unknown_practitioner_returns_resource_not_found(admin_session, tenant_context):
    install_overrides(admin_session, tenant_context)
    client = TestClient(app)
    try:
        specialty = create_specialty(client, tenant_context)
        response = client.post(f"/api/admin/practitioners/{uuid4()}/specialties", json={"specialty_id": specialty["id"]}, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_assign_unknown_specialty_to_practitioner_returns_resource_not_found(admin_session, tenant_context):
    install_overrides(admin_session, tenant_context)
    client = TestClient(app)
    try:
        practitioner = create_practitioner(client, tenant_context)
        response = client.post(f"/api/admin/practitioners/{practitioner['id']}/specialties", json={"specialty_id": str(uuid4())}, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_duplicate_practitioner_specialty_assignment_does_not_create_duplicates(admin_session, tenant_context):
    install_overrides(admin_session, tenant_context)
    client = TestClient(app)
    try:
        practitioner = create_practitioner(client, tenant_context)
        specialty = create_specialty(client, tenant_context)
        payload = {"specialty_id": specialty["id"]}
        first = client.post(f"/api/admin/practitioners/{practitioner['id']}/specialties", json=payload, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
        second = client.post(f"/api/admin/practitioners/{practitioner['id']}/specialties", json=payload, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()
    assert first.status_code == 200
    assert second.status_code == 200
    count = len(admin_session.scalars(select(PractitionerSpecialty)).all())
    assert count == 1


@pytest.mark.parametrize("path,method,json", [("/api/admin/practitioners", "post", practitioner_payload()), ("/api/admin/specialties", "post", specialty_payload())])
def test_missing_tenant_header_returns_authentication_required_for_practitioner_and_specialty_endpoints(path, method, json):
    response = getattr(TestClient(app), method)(path, json=json)
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"

def test_patch_disable_activate_specialty_and_duplicate_name(admin_session, tenant_context):
    install_overrides(admin_session, tenant_context)
    client = TestClient(app)
    try:
        specialty = create_specialty(client, tenant_context, "  Pediatría  ")
        patched = client.patch(f"/api/admin/specialties/{specialty['id']}", json={"name": "Pediatría clínica"}, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
        disabled = client.post(f"/api/admin/specialties/{specialty['id']}/disable", json={}, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
        activated = client.patch(f"/api/admin/specialties/{specialty['id']}", json={"status": "active"}, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
        duplicate = client.post("/api/admin/specialties", json=specialty_payload("Pediatría clínica"), headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()
    assert patched.status_code == 200
    assert patched.json()["data"]["name"] == "Pediatría clínica"
    assert disabled.json()["data"]["status"] == "inactive"
    assert activated.json()["data"]["status"] == "active"
    assert duplicate.status_code == 409


def test_list_disable_and_restore_practitioner_specialty(admin_session, tenant_context):
    install_overrides(admin_session, tenant_context)
    client = TestClient(app)
    try:
        practitioner = create_practitioner(client, tenant_context)
        pediatrics = create_specialty(client, tenant_context, "Pediatría")
        nephrology = create_specialty(client, tenant_context, "Nefrología")
        for specialty in (pediatrics, nephrology):
            response = client.post(f"/api/admin/practitioners/{practitioner['id']}/specialties", json={"specialty_id": specialty["id"]}, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
            assert response.status_code == 200
        listed = client.get(f"/api/admin/practitioners/{practitioner['id']}/specialties", headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
        disabled = client.post(f"/api/admin/practitioners/{practitioner['id']}/specialties/{nephrology['id']}/disable", json={}, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
        restored = client.post(f"/api/admin/practitioners/{practitioner['id']}/specialties", json={"specialty_id": nephrology["id"]}, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()
    assert listed.status_code == 200
    assert [item["specialty_name"] for item in listed.json()["data"]] == ["Nefrología", "Pediatría"]
    assert disabled.json()["data"]["status"] == "inactive"
    assert restored.json()["data"]["status"] == "active"
    assert len(admin_session.scalars(select(PractitionerSpecialty)).all()) == 2


def test_inactive_specialty_cannot_be_newly_assigned(admin_session, tenant_context):
    install_overrides(admin_session, tenant_context)
    client = TestClient(app)
    try:
        practitioner = create_practitioner(client, tenant_context)
        specialty = create_specialty(client, tenant_context, "Pediatría")
        client.post(f"/api/admin/specialties/{specialty['id']}/disable", json={}, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
        response = client.post(f"/api/admin/practitioners/{practitioner['id']}/specialties", json={"specialty_id": specialty["id"]}, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()
    assert response.status_code == 409


def test_sync_practitioner_specialties_success_creates_reactivates_and_inactivates(admin_session, tenant_context):
    install_overrides(admin_session, tenant_context)
    client = TestClient(app)
    try:
        practitioner = create_practitioner(client, tenant_context)
        pediatrics = create_specialty(client, tenant_context, "Pediatría")
        nephrology = create_specialty(client, tenant_context, "Nefrología")
        cardiology = create_specialty(client, tenant_context, "Cardiología")
        client.post(f"/api/admin/practitioners/{practitioner['id']}/specialties", json={"specialty_id": cardiology["id"]}, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
        client.post(f"/api/admin/practitioners/{practitioner['id']}/specialties/{cardiology['id']}/disable", json={}, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
        client.post(f"/api/admin/practitioners/{practitioner['id']}/specialties", json={"specialty_id": pediatrics["id"]}, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
        response = client.put(
            f"/api/admin/practitioners/{practitioner['id']}/specialties",
            json={"specialty_ids": [nephrology["id"], cardiology["id"]]},
            headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)},
        )
        listed = client.get(f"/api/admin/practitioners/{practitioner['id']}/specialties", headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()
    assert response.status_code == 200
    assert [item["specialty_name"] for item in response.json()["data"]] == ["Cardiología", "Nefrología"]
    by_name = {item["specialty_name"]: item["status"] for item in listed.json()["data"]}
    assert by_name == {"Cardiología": "active", "Nefrología": "active", "Pediatría": "inactive"}
    assert len(admin_session.scalars(select(PractitionerSpecialty)).all()) == 3


def test_sync_practitioner_specialties_empty_payload_removes_active_assignments(admin_session, tenant_context):
    install_overrides(admin_session, tenant_context)
    client = TestClient(app)
    try:
        practitioner = create_practitioner(client, tenant_context)
        specialty = create_specialty(client, tenant_context, "Pediatría")
        client.post(f"/api/admin/practitioners/{practitioner['id']}/specialties", json={"specialty_id": specialty["id"]}, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
        response = client.put(f"/api/admin/practitioners/{practitioner['id']}/specialties", json={"specialty_ids": []}, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
        active = client.get(f"/api/admin/practitioners/{practitioner['id']}/specialties?include_inactive=false", headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()
    assert response.status_code == 200
    assert response.json()["data"] == []
    assert active.json()["data"] == []


def test_sync_practitioner_specialties_rejects_duplicate_ids(admin_session, tenant_context):
    install_overrides(admin_session, tenant_context)
    client = TestClient(app)
    try:
        practitioner = create_practitioner(client, tenant_context)
        specialty = create_specialty(client, tenant_context, "Pediatría")
        response = client.put(
            f"/api/admin/practitioners/{practitioner['id']}/specialties",
            json={"specialty_ids": [specialty["id"], specialty["id"]]},
            headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)},
        )
    finally:
        clear_overrides()
    assert response.status_code == 422
    assert len(admin_session.scalars(select(PractitionerSpecialty)).all()) == 0


def test_sync_practitioner_specialties_rejects_unknown_or_inactive_entities(admin_session, tenant_context):
    install_overrides(admin_session, tenant_context)
    client = TestClient(app)
    try:
        practitioner = create_practitioner(client, tenant_context)
        inactive = create_specialty(client, tenant_context, "Pediatría")
        client.post(f"/api/admin/specialties/{inactive['id']}/disable", json={}, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
        unknown_practitioner = client.put(
            f"/api/admin/practitioners/{uuid4()}/specialties",
            json={"specialty_ids": []},
            headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)},
        )
        unknown_specialty = client.put(
            f"/api/admin/practitioners/{practitioner['id']}/specialties",
            json={"specialty_ids": [str(uuid4())]},
            headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)},
        )
        inactive_specialty = client.put(
            f"/api/admin/practitioners/{practitioner['id']}/specialties",
            json={"specialty_ids": [inactive["id"]]},
            headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)},
        )
    finally:
        clear_overrides()
    assert unknown_practitioner.status_code == 404
    assert unknown_specialty.status_code == 404
    assert inactive_specialty.status_code == 409
    assert len(admin_session.scalars(select(PractitionerSpecialty)).all()) == 0


def test_sync_practitioner_specialties_rolls_back_when_any_specialty_is_invalid(admin_session, tenant_context):
    install_overrides(admin_session, tenant_context)
    client = TestClient(app)
    try:
        practitioner = create_practitioner(client, tenant_context)
        valid = create_specialty(client, tenant_context, "Pediatría")
        response = client.put(
            f"/api/admin/practitioners/{practitioner['id']}/specialties",
            json={"specialty_ids": [valid["id"], str(uuid4())]},
            headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)},
        )
    finally:
        clear_overrides()
    assert response.status_code == 404
    assert len(admin_session.scalars(select(PractitionerSpecialty)).all()) == 0


def test_list_include_inactive_false_and_inactive_master_remains_visible(admin_session, tenant_context):
    install_overrides(admin_session, tenant_context)
    client = TestClient(app)
    try:
        practitioner = create_practitioner(client, tenant_context)
        pediatrics = create_specialty(client, tenant_context, "Pediatría")
        nephrology = create_specialty(client, tenant_context, "Nefrología")
        client.post(f"/api/admin/practitioners/{practitioner['id']}/specialties", json={"specialty_id": pediatrics["id"]}, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
        client.post(f"/api/admin/practitioners/{practitioner['id']}/specialties", json={"specialty_id": nephrology["id"]}, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
        client.post(f"/api/admin/practitioners/{practitioner['id']}/specialties/{nephrology['id']}/disable", json={}, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
        client.post(f"/api/admin/specialties/{pediatrics['id']}/disable", json={}, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
        active_only = client.get(f"/api/admin/practitioners/{practitioner['id']}/specialties?include_inactive=false", headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()
    assert active_only.status_code == 200
    assert len(active_only.json()["data"]) == 1
    assert active_only.json()["data"][0]["specialty_name"] == "Pediatría"
    assert active_only.json()["data"][0]["specialty_status"] == "inactive"
