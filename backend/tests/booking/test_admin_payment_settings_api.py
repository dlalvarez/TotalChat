from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.admin.dependencies import get_admin_tenant_context, get_db_session
from app.main import app
from app.models.tenant import Organization, PaymentSettings
from app.tenancy.context import TenantContext

TENANT_TABLES = [Organization.__table__, PaymentSettings.__table__]


@pytest.fixture()
def tenant_context():
    return TenantContext(tenant_id=uuid4(), slug="clinica-vida", schema_name="tenant_clinica_vida")


@pytest.fixture()
def payment_settings_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    for table in TENANT_TABLES:
        table.create(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture()
def organization(payment_settings_session):
    org = Organization(name="Clínica Vida", organization_type="clinic")
    other = Organization(name="Clínica Norte", organization_type="clinic")
    payment_settings_session.add_all([org, other])
    payment_settings_session.commit()
    return org


def clear_overrides() -> None:
    app.dependency_overrides.clear()


def install_overrides(session, tenant_context, include_tenant=True):
    def override_session():
        yield session

    app.dependency_overrides[get_db_session] = override_session
    if include_tenant:
        app.dependency_overrides[get_admin_tenant_context] = lambda: tenant_context


def payment_settings_payload(organization, **overrides):
    payload = {
        "organization_id": str(organization.id),
        "allow_transfer": True,
        "allow_simulated_payment": True,
        "allow_pay_on_site": False,
        "evidence_deadline_minutes": 90,
        "manual_review_deadline_minutes": 1440,
        "release_slot_on_missing_evidence": True,
        "status": "active",
    }
    payload.update(overrides)
    return payload


def request(method, path, session, tenant_context, *, json=None, include_tenant=True):
    install_overrides(session, tenant_context, include_tenant=include_tenant)
    try:
        return TestClient(app).request(method, path, json=json, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()


def test_post_creates_payment_settings_for_valid_organization(payment_settings_session, tenant_context, organization):
    response = request("POST", "/api/admin/payment-settings", payment_settings_session, tenant_context, json=payment_settings_payload(organization))
    assert response.status_code == 200
    data = response.json()["data"]
    assert UUID(data["id"])
    assert data["organization_id"] == str(organization.id)
    assert data["evidence_deadline_minutes"] == 90
    assert data["manual_review_deadline_minutes"] == 1440
    assert "schema_name" not in data


def test_post_rejects_missing_tenant_header(payment_settings_session, tenant_context, organization):
    install_overrides(payment_settings_session, tenant_context, include_tenant=False)
    try:
        response = TestClient(app).post("/api/admin/payment-settings", json=payment_settings_payload(organization))
    finally:
        clear_overrides()
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


def test_post_rejects_schema_name_in_payload(payment_settings_session, tenant_context, organization):
    response = request("POST", "/api/admin/payment-settings", payment_settings_session, tenant_context, json=payment_settings_payload(organization, schema_name="tenant_x"))
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_post_rejects_unknown_organization_id(payment_settings_session, tenant_context, organization):
    response = request("POST", "/api/admin/payment-settings", payment_settings_session, tenant_context, json=payment_settings_payload(organization, organization_id=str(uuid4())))
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


@pytest.mark.parametrize("field", ["evidence_deadline_minutes", "manual_review_deadline_minutes"])
def test_post_rejects_invalid_deadlines(payment_settings_session, tenant_context, organization, field):
    response = request("POST", "/api/admin/payment-settings", payment_settings_session, tenant_context, json=payment_settings_payload(organization, **{field: 0}))
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_post_defaults_release_slot_on_review_overdue_to_false(payment_settings_session, tenant_context, organization):
    payload = payment_settings_payload(organization)
    payload.pop("release_slot_on_review_overdue", None)
    response = request("POST", "/api/admin/payment-settings", payment_settings_session, tenant_context, json=payload)
    assert response.status_code == 200
    assert response.json()["data"]["release_slot_on_review_overdue"] is False


def test_get_lists_payment_settings_for_tenant(payment_settings_session, tenant_context, organization):
    created = request("POST", "/api/admin/payment-settings", payment_settings_session, tenant_context, json=payment_settings_payload(organization)).json()["data"]
    response = request("GET", "/api/admin/payment-settings", payment_settings_session, tenant_context)
    assert response.status_code == 200
    assert [item["id"] for item in response.json()["data"]] == [created["id"]]
    assert "schema_name" not in response.json()["data"][0]


def test_get_filters_by_organization_id(payment_settings_session, tenant_context, organization):
    org2 = payment_settings_session.query(Organization).filter(Organization.id != organization.id).one()
    request("POST", "/api/admin/payment-settings", payment_settings_session, tenant_context, json=payment_settings_payload(organization))
    request("POST", "/api/admin/payment-settings", payment_settings_session, tenant_context, json=payment_settings_payload(org2))
    response = request("GET", f"/api/admin/payment-settings?organization_id={organization.id}", payment_settings_session, tenant_context)
    assert response.status_code == 200
    assert len(response.json()["data"]) == 1
    assert response.json()["data"][0]["organization_id"] == str(organization.id)


def test_patch_updates_allowed_configurable_fields(payment_settings_session, tenant_context, organization):
    created = request("POST", "/api/admin/payment-settings", payment_settings_session, tenant_context, json=payment_settings_payload(organization)).json()["data"]
    response = request("PATCH", f"/api/admin/payment-settings/{created['id']}", payment_settings_session, tenant_context, json={"allow_pay_on_site": True, "release_slot_on_review_overdue": True, "status": "inactive"})
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["allow_pay_on_site"] is True
    assert data["release_slot_on_review_overdue"] is True
    assert data["status"] == "inactive"
    assert data["organization_id"] == str(organization.id)


def test_patch_rejects_schema_name(payment_settings_session, tenant_context, organization):
    created = request("POST", "/api/admin/payment-settings", payment_settings_session, tenant_context, json=payment_settings_payload(organization)).json()["data"]
    response = request("PATCH", f"/api/admin/payment-settings/{created['id']}", payment_settings_session, tenant_context, json={"schema_name": "tenant_x"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.parametrize("payload", [{"evidence_deadline_minutes": 0}, {"manual_review_deadline_minutes": 0}])
def test_patch_rejects_invalid_deadlines(payment_settings_session, tenant_context, organization, payload):
    created = request("POST", "/api/admin/payment-settings", payment_settings_session, tenant_context, json=payment_settings_payload(organization)).json()["data"]
    response = request("PATCH", f"/api/admin/payment-settings/{created['id']}", payment_settings_session, tenant_context, json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_patch_unknown_payment_settings_id_returns_resource_not_found(payment_settings_session, tenant_context):
    response = request("PATCH", f"/api/admin/payment-settings/{uuid4()}", payment_settings_session, tenant_context, json={"allow_transfer": False})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"
