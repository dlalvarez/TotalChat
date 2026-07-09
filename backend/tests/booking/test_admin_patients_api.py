from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.admin.dependencies import get_admin_tenant_context, get_db_session
from app.main import app
from app.models.tenant import Patient, PatientPayerProfile, Payer, PayerPlan, PayerType
from app.tenancy.context import TenantContext

TENANT_TABLES = [Patient.__table__, PayerType.__table__, Payer.__table__, PayerPlan.__table__, PatientPayerProfile.__table__]


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


def headers(ctx):
    return {"X-TotalChat-Tenant-Id": str(ctx.tenant_id)}


@pytest.fixture()
def payer_plan(admin_session):
    payer_type = PayerType(code="particular", name="Particular")
    payer = Payer(payer_type=payer_type, name="Particular")
    plan = PayerPlan(payer=payer, name="Tarifa particular")
    admin_session.add_all([payer_type, payer, plan])
    admin_session.flush()
    return plan


def test_create_patient_successfully_with_minimal_payload(admin_session, tenant_context):
    install_overrides(admin_session, tenant_context)
    try:
        response = TestClient(app).post("/api/admin/patients", json={"full_name": "María Gómez"}, headers=headers(tenant_context))
    finally:
        clear_overrides()

    assert response.status_code == 200
    data = response.json()["data"]
    assert UUID(data["id"])
    assert data["full_name"] == "María Gómez"
    assert data["status"] == "minimal"
    assert data["document_type"] is None
    assert "schema_name" not in data


def test_create_patient_successfully_with_optional_contact_and_document_fields(admin_session, tenant_context):
    payload = {
        "full_name": "María Gómez",
        "document_type": "CC",
        "document_number": "123456789",
        "email": "maria@example.com",
        "phone": "+573001112233",
    }
    install_overrides(admin_session, tenant_context)
    try:
        response = TestClient(app).post("/api/admin/patients", json=payload, headers=headers(tenant_context))
    finally:
        clear_overrides()

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["document_type"] == "CC"
    assert data["document_number"] == "123456789"
    assert data["email"] == "maria@example.com"
    assert data["phone"] == "+573001112233"
    assert "schema_name" not in data


def test_create_patient_rejects_schema_name(admin_session, tenant_context):
    install_overrides(admin_session, tenant_context)
    try:
        response = TestClient(app).post("/api/admin/patients", json={"full_name": "Evil", "schema_name": "tenant_evil"}, headers=headers(tenant_context))
    finally:
        clear_overrides()

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_create_patient_payer_profile_successfully(admin_session, tenant_context, payer_plan):
    patient = Patient(full_name="María Gómez")
    admin_session.add(patient)
    admin_session.flush()
    payload = {
        "payer_plan_id": str(payer_plan.id),
        "member_id": "ABC123",
        "authorization_required": False,
        "notes": "Plan vigente según información suministrada por el paciente.",
    }
    install_overrides(admin_session, tenant_context)
    try:
        response = TestClient(app).post(f"/api/admin/patients/{patient.id}/payer-profiles", json=payload, headers=headers(tenant_context))
    finally:
        clear_overrides()

    assert response.status_code == 200
    data = response.json()["data"]
    assert UUID(data["id"])
    assert data["patient_id"] == str(patient.id)
    assert data["payer_plan_id"] == str(payer_plan.id)
    assert data["member_id"] == "ABC123"
    assert data["authorization_required"] is False
    assert data["status"] == "active"
    assert "schema_name" not in data


def test_create_patient_payer_profile_rejects_schema_name(admin_session, tenant_context, payer_plan):
    patient = Patient(full_name="María Gómez")
    admin_session.add(patient)
    admin_session.flush()
    install_overrides(admin_session, tenant_context)
    try:
        response = TestClient(app).post(
            f"/api/admin/patients/{patient.id}/payer-profiles",
            json={"payer_plan_id": str(payer_plan.id), "schema_name": "tenant_evil"},
            headers=headers(tenant_context),
        )
    finally:
        clear_overrides()

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_create_patient_payer_profile_with_unknown_patient_returns_resource_not_found(admin_session, tenant_context, payer_plan):
    install_overrides(admin_session, tenant_context)
    try:
        response = TestClient(app).post(f"/api/admin/patients/{uuid4()}/payer-profiles", json={"payer_plan_id": str(payer_plan.id)}, headers=headers(tenant_context))
    finally:
        clear_overrides()

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_create_patient_payer_profile_with_unknown_payer_plan_returns_resource_not_found(admin_session, tenant_context):
    patient = Patient(full_name="María Gómez")
    admin_session.add(patient)
    admin_session.flush()
    install_overrides(admin_session, tenant_context)
    try:
        response = TestClient(app).post(f"/api/admin/patients/{patient.id}/payer-profiles", json={"payer_plan_id": str(uuid4())}, headers=headers(tenant_context))
    finally:
        clear_overrides()

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_missing_tenant_header_returns_authentication_required_for_patient_endpoints(admin_session, tenant_context):
    patient = Patient(full_name="María Gómez")
    admin_session.add(patient)
    admin_session.flush()

    def override_session():
        yield admin_session

    app.dependency_overrides[get_db_session] = override_session
    try:
        client = TestClient(app)
        patient_response = client.post("/api/admin/patients", json={"full_name": "María Gómez"})
        profile_response = client.post(f"/api/admin/patients/{patient.id}/payer-profiles", json={"payer_plan_id": str(uuid4())})
    finally:
        clear_overrides()

    assert patient_response.status_code == 401
    assert patient_response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"
    assert profile_response.status_code == 401
    assert profile_response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"
