from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
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


def headers(tenant_context):
    return {"X-Tenant-ID": str(tenant_context.tenant_id)}


def client(admin_session, tenant_context):
    install_overrides(admin_session, tenant_context)
    return TestClient(app)


@pytest.fixture(autouse=True)
def cleanup_overrides():
    clear_overrides()
    yield
    clear_overrides()


def seed_patient(session: Session, **kwargs) -> Patient:
    patient = Patient(full_name=kwargs.pop("full_name", "María Gómez"), **kwargs)
    session.add(patient)
    session.commit()
    session.refresh(patient)
    return patient


def assert_no_schema_name(payload: dict):
    assert "schema_name" not in payload
    assert "tenant" not in payload


def test_list_patients_includes_active_and_inactive(admin_session, tenant_context):
    active = seed_patient(admin_session, full_name="Ana Activa", profile_status="minimal")
    inactive = seed_patient(admin_session, full_name="Ina Inactiva", profile_status="inactive")
    response = client(admin_session, tenant_context).get("/api/admin/patients", headers=headers(tenant_context))
    assert response.status_code == 200
    ids = {row["id"] for row in response.json()["data"]}
    assert ids == {str(active.id), str(inactive.id)}
    for row in response.json()["data"]:
        assert_no_schema_name(row)


def test_get_patient_detail_and_404(admin_session, tenant_context):
    patient = seed_patient(admin_session, document_number="123")
    api = client(admin_session, tenant_context)
    ok = api.get(f"/api/admin/patients/{patient.id}", headers=headers(tenant_context))
    assert ok.status_code == 200
    assert ok.json()["data"]["document_number"] == "123"
    assert_no_schema_name(ok.json()["data"])
    missing = api.get(f"/api/admin/patients/{uuid4()}", headers=headers(tenant_context))
    assert missing.status_code == 404


def test_create_patient_defaults_to_admin_minimal_and_rejects_bad_payloads(admin_session, tenant_context):
    api = client(admin_session, tenant_context)
    response = api.post("/api/admin/patients", json={"full_name": "  Juan Pérez  ", "email": "juan@example.com", "document_type": "cc"}, headers=headers(tenant_context))
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["full_name"] == "Juan Pérez"
    assert data["profile_status"] == "minimal"
    assert data["document_type"] == "CC"
    assert data["created_from_channel"] == "admin"
    assert_no_schema_name(data)

    null_document_response = api.post("/api/admin/patients", json={"full_name": "Sin Documento", "document_type": None}, headers=headers(tenant_context))
    assert null_document_response.status_code == 200
    assert null_document_response.json()["data"]["document_type"] is None
    allowed_document_response = api.post("/api/admin/patients", json={"full_name": "Con Documento", "document_type": "CC"}, headers=headers(tenant_context))
    assert allowed_document_response.status_code == 200
    assert allowed_document_response.json()["data"]["document_type"] == "CC"

    assert api.post("/api/admin/patients", json={"full_name": "Evil", "schema_name": "tenant_evil"}, headers=headers(tenant_context)).status_code == 422
    assert api.post("/api/admin/patients", json={"full_name": "Evil", "unexpected": True}, headers=headers(tenant_context)).status_code == 422
    assert api.post("/api/admin/patients", json={"phone": "+57"}, headers=headers(tenant_context)).status_code == 422
    assert api.post("/api/admin/patients", json={"full_name": "   "}, headers=headers(tenant_context)).status_code == 422
    assert api.post("/api/admin/patients", json={"full_name": "Evil", "document_type": "UNKNOWN"}, headers=headers(tenant_context)).status_code == 422


def test_patch_patient_updates_basic_fields_and_validates_payload(admin_session, tenant_context):
    patient = seed_patient(admin_session, phone="1")
    api = client(admin_session, tenant_context)
    response = api.patch(
        f"/api/admin/patients/{patient.id}",
        json={"full_name": "María Editada", "phone": "2", "document_type": "PAS", "profile_status": "complete"},
        headers=headers(tenant_context),
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["full_name"] == "María Editada"
    assert data["phone"] == "2"
    assert data["document_type"] == "PAS"
    assert data["profile_status"] == "complete"
    assert_no_schema_name(data)

    assert api.patch(f"/api/admin/patients/{patient.id}", json={"schema_name": "tenant_evil"}, headers=headers(tenant_context)).status_code == 422
    assert api.patch(f"/api/admin/patients/{patient.id}", json={"unexpected": True}, headers=headers(tenant_context)).status_code == 422
    assert api.patch(f"/api/admin/patients/{patient.id}", json={"profile_status": "deleted"}, headers=headers(tenant_context)).status_code == 422
    null_patch_response = api.patch(f"/api/admin/patients/{patient.id}", json={"document_type": None}, headers=headers(tenant_context))
    assert null_patch_response.status_code == 200
    assert null_patch_response.json()["data"]["document_type"] is None
    assert api.patch(f"/api/admin/patients/{patient.id}", json={"document_type": "UNKNOWN"}, headers=headers(tenant_context)).status_code == 422
    assert api.patch(f"/api/admin/patients/{uuid4()}", json={"full_name": "Nada"}, headers=headers(tenant_context)).status_code == 404


def test_disable_is_logical_idempotent_and_reactivation_uses_patch(admin_session, tenant_context):
    patient = seed_patient(admin_session, profile_status="verified")
    api = client(admin_session, tenant_context)
    disabled = api.post(f"/api/admin/patients/{patient.id}/disable", json={}, headers=headers(tenant_context))
    assert disabled.status_code == 200
    assert disabled.json()["data"]["profile_status"] == "inactive"
    again = api.post(f"/api/admin/patients/{patient.id}/disable", json={}, headers=headers(tenant_context))
    assert again.status_code == 200
    assert again.json()["data"]["profile_status"] == "inactive"
    assert api.post(f"/api/admin/patients/{uuid4()}/disable", json={}, headers=headers(tenant_context)).status_code == 404

    listed = api.get("/api/admin/patients", headers=headers(tenant_context)).json()["data"]
    assert str(patient.id) in {row["id"] for row in listed}
    assert admin_session.scalar(select(Patient).where(Patient.id == patient.id)) is not None

    reactivated = api.patch(f"/api/admin/patients/{patient.id}", json={"profile_status": "minimal"}, headers=headers(tenant_context))
    assert reactivated.status_code == 200
    assert reactivated.json()["data"]["profile_status"] == "minimal"


def test_patient_filters(admin_session, tenant_context):
    p1 = seed_patient(admin_session, full_name="Carlos Filtro", document_number="ABC123", phone="300111", email="carlos@example.com", profile_status="minimal")
    p2 = seed_patient(admin_session, full_name="Laura Verificada", document_number="XYZ", phone="300222", email="laura@example.com", profile_status="verified")
    api = client(admin_session, tenant_context)
    assert [row["id"] for row in api.get("/api/admin/patients?q=filtro", headers=headers(tenant_context)).json()["data"]] == [str(p1.id)]
    assert [row["id"] for row in api.get("/api/admin/patients?q=ABC123", headers=headers(tenant_context)).json()["data"]] == [str(p1.id)]
    assert [row["id"] for row in api.get("/api/admin/patients?q=laura@example.com", headers=headers(tenant_context)).json()["data"]] == [str(p2.id)]
    assert [row["id"] for row in api.get("/api/admin/patients?profile_status=verified", headers=headers(tenant_context)).json()["data"]] == [str(p2.id)]
    invalid_status_response = api.get("/api/admin/patients?profile_status=deleted", headers=headers(tenant_context))
    assert invalid_status_response.status_code == 400
    assert invalid_status_response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_create_patient_payer_profile_keeps_existing_contract(admin_session, tenant_context):
    patient = seed_patient(admin_session)
    payer_type = PayerType(code="particular", name="Particular")
    admin_session.add(payer_type)
    admin_session.flush()
    payer = Payer(payer_type_id=payer_type.id, name="Particular")
    admin_session.add(payer)
    admin_session.flush()
    payer_plan = PayerPlan(payer_id=payer.id, name="Tarifa particular")
    admin_session.add(payer_plan)
    admin_session.commit()

    response = client(admin_session, tenant_context).post(
        f"/api/admin/patients/{patient.id}/payer-profiles",
        json={"payer_plan_id": str(payer_plan.id), "member_id": "M-1"},
        headers=headers(tenant_context),
    )
    assert response.status_code == 200
    assert response.json()["data"]["member_id"] == "M-1"
