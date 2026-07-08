from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.admin.dependencies import get_admin_tenant_context, get_db_session
from app.main import app
from app.models.tenant import Organization, Payer, PayerPlan, PayerType, Practitioner, PractitionerService, PractitionerServicePrice
from app.tenancy.context import TenantContext

TENANT_TABLES = [Organization.__table__, Practitioner.__table__, PractitionerService.__table__, PayerType.__table__, Payer.__table__, PayerPlan.__table__, PractitionerServicePrice.__table__]


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
    service = PractitionerService(organization=org, practitioner=practitioner, name="Consulta", duration_minutes=45)
    payer_type = PayerType(code="particular", name="Particular")
    payer = Payer(payer_type=payer_type, name="Particular")
    plan = PayerPlan(payer=payer, name="Tarifa particular")
    admin_session.add_all([org, practitioner, service, payer_type, payer, plan])
    admin_session.flush()
    return org, practitioner, service, payer_type, payer, plan


def headers(ctx):
    return {"X-TotalChat-Tenant-Id": str(ctx.tenant_id)}


def test_create_payer_type_successfully(admin_session, tenant_context):
    install_overrides(admin_session, tenant_context)
    try:
        response = TestClient(app).post("/api/admin/payer-types", json={"code": "medicina_prepagada", "name": "Medicina prepagada", "description": "Planes."}, headers=headers(tenant_context))
    finally:
        clear_overrides()
    assert response.status_code == 200
    data = response.json()["data"]
    assert UUID(data["id"])
    assert data["code"] == "medicina_prepagada"
    assert data["status"] == "active"
    assert "schema_name" not in data


def test_create_payer_type_rejects_schema_name(admin_session, tenant_context):
    install_overrides(admin_session, tenant_context)
    try:
        response = TestClient(app).post("/api/admin/payer-types", json={"code": "x", "name": "X", "schema_name": "tenant_x"}, headers=headers(tenant_context))
    finally:
        clear_overrides()
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_duplicate_payer_type_code_returns_conflict(admin_session, tenant_context):
    install_overrides(admin_session, tenant_context)
    client = TestClient(app)
    try:
        payload = {"code": "particular", "name": "Particular"}
        assert client.post("/api/admin/payer-types", json=payload, headers=headers(tenant_context)).status_code == 200
        response = client.post("/api/admin/payer-types", json=payload, headers=headers(tenant_context))
    finally:
        clear_overrides()
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CONFLICT"


def test_create_payer_success_and_unknown_and_rejects_schema_name(admin_session, tenant_context, base_data):
    _org, _practitioner, _service, payer_type, _payer, _plan = base_data
    install_overrides(admin_session, tenant_context)
    client = TestClient(app)
    try:
        response = client.post("/api/admin/payers", json={"payer_type_id": str(payer_type.id), "name": "Colsanitas", "description": "Entidad."}, headers=headers(tenant_context))
        missing = client.post("/api/admin/payers", json={"payer_type_id": str(uuid4()), "name": "Nope"}, headers=headers(tenant_context))
        extra = client.post("/api/admin/payers", json={"payer_type_id": str(payer_type.id), "name": "X", "schema_name": "tenant_x"}, headers=headers(tenant_context))
    finally:
        clear_overrides()
    assert response.status_code == 200
    assert response.json()["data"]["payer_type_id"] == str(payer_type.id)
    assert "schema_name" not in response.json()["data"]
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "RESOURCE_NOT_FOUND"
    assert extra.status_code == 422


def test_create_payer_plan_success_and_unknown_and_rejects_schema_name(admin_session, tenant_context, base_data):
    _org, _practitioner, _service, _payer_type, payer, _plan = base_data
    install_overrides(admin_session, tenant_context)
    client = TestClient(app)
    try:
        response = client.post("/api/admin/payer-plans", json={"payer_id": str(payer.id), "name": "Plan avanzado", "description": "Plan."}, headers=headers(tenant_context))
        missing = client.post("/api/admin/payer-plans", json={"payer_id": str(uuid4()), "name": "Nope"}, headers=headers(tenant_context))
        extra = client.post("/api/admin/payer-plans", json={"payer_id": str(payer.id), "name": "X", "schema_name": "tenant_x"}, headers=headers(tenant_context))
    finally:
        clear_overrides()
    assert response.status_code == 200
    assert response.json()["data"]["payer_id"] == str(payer.id)
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "RESOURCE_NOT_FOUND"
    assert extra.status_code == 422


def price_payload(service, plan, **overrides):
    payload = {"practitioner_service_id": str(service.id), "payer_plan_id": str(plan.id), "price": 100000, "currency": "COP", "valid_from": "2026-07-01", "valid_to": None}
    payload.update(overrides)
    return payload


def test_create_practitioner_service_price_validations(admin_session, tenant_context, base_data):
    _org, _practitioner, service, _payer_type, _payer, plan = base_data
    install_overrides(admin_session, tenant_context)
    client = TestClient(app)
    try:
        ok = client.post("/api/admin/practitioner-service-prices", json=price_payload(service, plan), headers=headers(tenant_context))
        extra = client.post("/api/admin/practitioner-service-prices", json=price_payload(service, plan, schema_name="tenant_x"), headers=headers(tenant_context))
        missing_service = client.post("/api/admin/practitioner-service-prices", json=price_payload(service, plan, practitioner_service_id=str(uuid4())), headers=headers(tenant_context))
        missing_plan = client.post("/api/admin/practitioner-service-prices", json=price_payload(service, plan, payer_plan_id=str(uuid4())), headers=headers(tenant_context))
        negative = client.post("/api/admin/practitioner-service-prices", json=price_payload(service, plan, price=-1), headers=headers(tenant_context))
        currency = client.post("/api/admin/practitioner-service-prices", json=price_payload(service, plan, currency="cop"), headers=headers(tenant_context))
        dates = client.post("/api/admin/practitioner-service-prices", json=price_payload(service, plan, valid_to="2026-06-30"), headers=headers(tenant_context))
    finally:
        clear_overrides()
    assert ok.status_code == 200
    data = ok.json()["data"]
    assert data["price"] == 100000
    assert data["valid_from"] == "2026-07-01"
    assert "schema_name" not in data
    assert extra.status_code == 422
    assert missing_service.status_code == 404
    assert missing_service.json()["error"]["code"] == "RESOURCE_NOT_FOUND"
    assert missing_plan.status_code == 404
    assert missing_plan.json()["error"]["code"] == "RESOURCE_NOT_FOUND"
    assert negative.status_code == 422
    assert negative.json()["error"]["code"] == "VALIDATION_ERROR"
    assert currency.status_code == 422
    assert dates.status_code == 422


def test_list_practitioner_service_prices_successfully_and_unknown_service(admin_session, tenant_context, base_data):
    _org, _practitioner, service, _payer_type, _payer, plan = base_data
    admin_session.add_all([
        PractitionerServicePrice(practitioner_service=service, payer_plan=plan, price=Decimal("100000.00"), currency="COP", valid_from=date(2026, 7, 1)),
        PractitionerServicePrice(practitioner_service=service, payer_plan=plan, price=Decimal("90000.50"), currency="COP", valid_from=date(2026, 6, 1), status="inactive"),
    ])
    admin_session.flush()
    install_overrides(admin_session, tenant_context)
    client = TestClient(app)
    try:
        response = client.get(f"/api/admin/practitioner-services/{service.id}/prices", headers=headers(tenant_context))
        missing = client.get(f"/api/admin/practitioner-services/{uuid4()}/prices", headers=headers(tenant_context))
    finally:
        clear_overrides()
    assert response.status_code == 200
    data = response.json()["data"]
    assert [item["valid_from"] for item in data] == ["2026-06-01", "2026-07-01"]
    assert data[0]["price"] == 90000.5
    assert all("schema_name" not in item for item in data)
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_missing_tenant_header_returns_authentication_required_for_payer_and_price_endpoints(admin_session, tenant_context):
    def override_session():
        yield admin_session

    app.dependency_overrides[get_db_session] = override_session
    try:
        client = TestClient(app)
        payer_type = client.post("/api/admin/payer-types", json={"code": "x", "name": "X"})
        price = client.post("/api/admin/practitioner-service-prices", json={})
    finally:
        clear_overrides()
    assert payer_type.status_code == 401
    assert payer_type.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"
    assert price.status_code == 401
    assert price.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"
