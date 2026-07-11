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

def test_payer_type_full_logical_crud_and_normalized_duplicate(admin_session, tenant_context):
    install_overrides(admin_session, tenant_context)
    client = TestClient(app)
    try:
        created = client.post("/api/admin/payer-types", json={"code": " Medicina Prepagada ", "name": " Medicina prepagada "}, headers=headers(tenant_context))
        duplicate = client.post("/api/admin/payer-types", json={"code": "medicina_prepagada", "name": "Otra"}, headers=headers(tenant_context))
        payer_type_id = created.json()["data"]["id"]
        listed = client.get("/api/admin/payer-types", headers=headers(tenant_context))
        one = client.get(f"/api/admin/payer-types/{payer_type_id}", headers=headers(tenant_context))
        patched = client.patch(f"/api/admin/payer-types/{payer_type_id}", json={"name": "Prepagada", "description": "Base"}, headers=headers(tenant_context))
        disabled = client.post(f"/api/admin/payer-types/{payer_type_id}/disable", json={}, headers=headers(tenant_context))
        reactivated = client.patch(f"/api/admin/payer-types/{payer_type_id}", json={"status": "active"}, headers=headers(tenant_context))
    finally:
        clear_overrides()
    assert created.status_code == 200
    assert created.json()["data"]["code"] == "medicina_prepagada"
    assert duplicate.status_code == 409
    assert listed.status_code == 200 and len(listed.json()["data"]) == 1
    assert one.status_code == 200
    assert patched.json()["data"]["name"] == "Prepagada"
    assert disabled.json()["data"]["status"] == "inactive"
    assert reactivated.json()["data"]["status"] == "active"


def test_payer_rules_visibility_and_safe_parent_serialization(admin_session, tenant_context, base_data):
    _org, _practitioner, _service, payer_type, payer, _plan = base_data
    install_overrides(admin_session, tenant_context)
    client = TestClient(app)
    try:
        created = client.post("/api/admin/payers", json={"payer_type_id": str(payer_type.id), "name": "Sura"}, headers=headers(tenant_context))
        duplicate = client.post("/api/admin/payers", json={"payer_type_id": str(payer_type.id), "name": " sura "}, headers=headers(tenant_context))
        payer_id = created.json()["data"]["id"]
        patched = client.patch(f"/api/admin/payers/{payer_id}", json={"name": "Sura póliza", "description": "Entidad"}, headers=headers(tenant_context))
        disabled = client.post(f"/api/admin/payers/{payer_id}/disable", json={}, headers=headers(tenant_context))
        client.post(f"/api/admin/payer-types/{payer_type.id}/disable", json={}, headers=headers(tenant_context))
        create_under_inactive = client.post("/api/admin/payers", json={"payer_type_id": str(payer_type.id), "name": "Colsanitas"}, headers=headers(tenant_context))
        reactivate_blocked = client.patch(f"/api/admin/payers/{payer_id}", json={"status": "active"}, headers=headers(tenant_context))
        listed = client.get("/api/admin/payers", headers=headers(tenant_context))
        missing = client.post("/api/admin/payers", json={"payer_type_id": str(uuid4()), "name": "Nope"}, headers=headers(tenant_context))
    finally:
        clear_overrides()
    assert duplicate.status_code == 409
    assert patched.json()["data"]["payer_type_name"] == "Particular"
    assert disabled.json()["data"]["payer_type_code"] == "particular"
    assert create_under_inactive.status_code == 409
    assert create_under_inactive.json()["error"]["code"] == "BUSINESS_RULE_VIOLATION"
    assert reactivate_blocked.status_code == 409
    assert reactivate_blocked.json()["error"]["code"] == "BUSINESS_RULE_VIOLATION"
    assert missing.status_code == 404
    assert any(item["id"] == payer_id and item["payer_type_status"] == "inactive" for item in listed.json()["data"])


def test_payer_plan_rules_visibility_and_safe_parent_serialization(admin_session, tenant_context, base_data):
    _org, _practitioner, _service, payer_type, payer, _plan = base_data
    install_overrides(admin_session, tenant_context)
    client = TestClient(app)
    try:
        created = client.post("/api/admin/payer-plans", json={"payer_id": str(payer.id), "name": "Póliza básica"}, headers=headers(tenant_context))
        duplicate = client.post("/api/admin/payer-plans", json={"payer_id": str(payer.id), "name": " póliza BÁSICA "}, headers=headers(tenant_context))
        plan_id = created.json()["data"]["id"]
        patched = client.patch(f"/api/admin/payer-plans/{plan_id}", json={"name": "Póliza plus", "description": "Plan"}, headers=headers(tenant_context))
        disabled = client.post(f"/api/admin/payer-plans/{plan_id}/disable", json={}, headers=headers(tenant_context))
        client.post(f"/api/admin/payers/{payer.id}/disable", json={}, headers=headers(tenant_context))
        create_under_inactive_payer = client.post("/api/admin/payer-plans", json={"payer_id": str(payer.id), "name": "Plan bloqueado"}, headers=headers(tenant_context))
        reactivate_blocked = client.patch(f"/api/admin/payer-plans/{plan_id}", json={"status": "active"}, headers=headers(tenant_context))
        client.patch(f"/api/admin/payers/{payer.id}", json={"status": "active"}, headers=headers(tenant_context))
        client.post(f"/api/admin/payer-types/{payer_type.id}/disable", json={}, headers=headers(tenant_context))
        create_under_inactive_type = client.post("/api/admin/payer-plans", json={"payer_id": str(payer.id), "name": "Plan tipo bloqueado"}, headers=headers(tenant_context))
        listed = client.get("/api/admin/payer-plans", headers=headers(tenant_context))
        missing = client.post("/api/admin/payer-plans", json={"payer_id": str(uuid4()), "name": "Nope"}, headers=headers(tenant_context))
    finally:
        clear_overrides()
    assert created.json()["data"]["payer_name"] == "Particular"
    assert duplicate.status_code == 409
    assert patched.json()["data"]["payer_type_code"] == "particular"
    assert disabled.json()["data"]["status"] == "inactive"
    assert create_under_inactive_payer.status_code == 409
    assert create_under_inactive_payer.json()["error"]["code"] == "BUSINESS_RULE_VIOLATION"
    assert reactivate_blocked.status_code == 409
    assert reactivate_blocked.json()["error"]["code"] == "BUSINESS_RULE_VIOLATION"
    assert create_under_inactive_type.status_code == 409
    assert create_under_inactive_type.json()["error"]["code"] == "BUSINESS_RULE_VIOLATION"
    assert missing.status_code == 404
    assert any(item["id"] == plan_id and item["payer_type_status"] == "inactive" for item in listed.json()["data"])


def assert_price_readable(data, service, org, practitioner, plan, payer, payer_type):
    assert data["practitioner_service_name"] == service.name
    assert data["organization_name"] == org.name
    assert data["practitioner_name"] == practitioner.full_name
    assert data["payer_plan_name"] == plan.name
    assert data["payer_name"] == payer.name
    assert data["payer_type_name"] == payer_type.name
    assert data["currency"] == "COP"
    assert data["status"] in {"active", "inactive"}
    assert "schema_name" not in data


def test_create_practitioner_service_price_success_with_readable_serialization(admin_session, tenant_context, base_data):
    org, practitioner, service, payer_type, payer, plan = base_data
    install_overrides(admin_session, tenant_context)
    client = TestClient(app)
    try:
        response = client.post("/api/admin/practitioner-service-prices", json=price_payload(service, plan), headers=headers(tenant_context))
    finally:
        clear_overrides()
    assert response.status_code == 200
    data = response.json()["data"]
    assert UUID(data["id"])
    assert data["price"] == 100000
    assert data["valid_from"] == "2026-07-01"
    assert data["valid_to"] is None
    assert data["status"] == "active"
    assert_price_readable(data, service, org, practitioner, plan, payer, payer_type)


def test_practitioner_service_price_missing_resources_return_404(admin_session, tenant_context, base_data):
    _org, _practitioner, service, _payer_type, _payer, plan = base_data
    price = PractitionerServicePrice(practitioner_service=service, payer_plan=plan, price=Decimal("100000.00"), currency="COP", valid_from=date(2026, 1, 1))
    admin_session.add(price)
    admin_session.flush()
    install_overrides(admin_session, tenant_context)
    client = TestClient(app)
    try:
        missing_service_create = client.post("/api/admin/practitioner-service-prices", json=price_payload(service, plan, practitioner_service_id=str(uuid4()), valid_from="2026-02-01"), headers=headers(tenant_context))
        missing_plan_create = client.post("/api/admin/practitioner-service-prices", json=price_payload(service, plan, payer_plan_id=str(uuid4()), valid_from="2026-02-01"), headers=headers(tenant_context))
        missing_detail = client.get(f"/api/admin/practitioner-service-prices/{uuid4()}", headers=headers(tenant_context))
        missing_disable = client.post(f"/api/admin/practitioner-service-prices/{uuid4()}/disable", json={}, headers=headers(tenant_context))
        missing_service_list = client.get(f"/api/admin/practitioner-services/{uuid4()}/prices", headers=headers(tenant_context))
    finally:
        clear_overrides()
    for response in [missing_service_create, missing_plan_create, missing_detail, missing_disable, missing_service_list]:
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


@pytest.mark.parametrize(
    ("field", "message_fragment"),
    [
        ("service", "service"),
        ("plan", "plan"),
        ("payer", "payer"),
        ("payer_type", "payer type"),
    ],
)
def test_create_practitioner_service_price_rejects_inactive_parents(admin_session, tenant_context, base_data, field, message_fragment):
    _org, _practitioner, service, payer_type, payer, plan = base_data
    if field == "service":
        service.status = "inactive"
    elif field == "plan":
        plan.status = "inactive"
    elif field == "payer":
        payer.status = "inactive"
    else:
        payer_type.status = "inactive"
    admin_session.flush()
    install_overrides(admin_session, tenant_context)
    try:
        response = TestClient(app).post("/api/admin/practitioner-service-prices", json=price_payload(service, plan), headers=headers(tenant_context))
    finally:
        clear_overrides()
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "BUSINESS_RULE_VIOLATION"
    assert message_fragment in response.json()["error"]["message"].lower()


@pytest.mark.parametrize(
    "payload_overrides",
    [
        {"currency": "CO"},
        {"currency": "cop"},
        {"price": -1},
        {"valid_to": "2026-06-30"},
    ],
)
def test_practitioner_service_price_payload_validation_errors(admin_session, tenant_context, base_data, payload_overrides):
    _org, _practitioner, service, _payer_type, _payer, plan = base_data
    install_overrides(admin_session, tenant_context)
    try:
        response = TestClient(app).post("/api/admin/practitioner-service-prices", json=price_payload(service, plan, **payload_overrides), headers=headers(tenant_context))
    finally:
        clear_overrides()
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def seed_filter_prices(admin_session, base_data):
    org, practitioner, service, payer_type, payer, plan = base_data
    org2 = Organization(name="Clínica Norte", organization_type="clinic")
    practitioner2 = Practitioner(full_name="Dr. Carlos Ruiz")
    service2 = PractitionerService(organization=org2, practitioner=practitioner2, name="Control", duration_minutes=30)
    payer_type2 = PayerType(code="prepagada", name="Medicina prepagada")
    payer2 = Payer(payer_type=payer_type2, name="Colsanitas")
    plan2 = PayerPlan(payer=payer2, name="Plan Integral")
    active_price = PractitionerServicePrice(practitioner_service=service, payer_plan=plan, price=Decimal("100000.00"), currency="COP", valid_from=date(2026, 1, 1), valid_to=date(2026, 1, 31), status="active")
    inactive_price = PractitionerServicePrice(practitioner_service=service, payer_plan=plan, price=Decimal("90000.00"), currency="COP", valid_from=date(2025, 1, 1), valid_to=date(2025, 1, 31), status="inactive")
    other_price = PractitionerServicePrice(practitioner_service=service2, payer_plan=plan2, price=Decimal("150000.00"), currency="COP", valid_from=date(2026, 2, 1), valid_to=date(2026, 2, 28), status="active")
    admin_session.add_all([org2, practitioner2, service2, payer_type2, payer2, plan2, active_price, inactive_price, other_price])
    admin_session.flush()
    return {
        "org": org,
        "practitioner": practitioner,
        "service": service,
        "payer_type": payer_type,
        "payer": payer,
        "plan": plan,
        "active_price": active_price,
        "inactive_price": inactive_price,
        "other_price": other_price,
    }


def test_list_practitioner_service_prices_general_filters_and_status_validation(admin_session, tenant_context, base_data):
    data = seed_filter_prices(admin_session, base_data)
    install_overrides(admin_session, tenant_context)
    client = TestClient(app)
    try:
        all_prices = client.get("/api/admin/practitioner-service-prices", headers=headers(tenant_context))
        active = client.get("/api/admin/practitioner-service-prices?status=active", headers=headers(tenant_context))
        inactive = client.get("/api/admin/practitioner-service-prices?status=inactive", headers=headers(tenant_context))
        include_inactive_false = client.get("/api/admin/practitioner-service-prices?include_inactive=false", headers=headers(tenant_context))
        by_org = client.get(f"/api/admin/practitioner-service-prices?organization_id={data['org'].id}", headers=headers(tenant_context))
        by_practitioner = client.get(f"/api/admin/practitioner-service-prices?practitioner_id={data['practitioner'].id}", headers=headers(tenant_context))
        by_service = client.get(f"/api/admin/practitioner-service-prices?practitioner_service_id={data['service'].id}", headers=headers(tenant_context))
        by_payer_type = client.get(f"/api/admin/practitioner-service-prices?payer_type_id={data['payer_type'].id}", headers=headers(tenant_context))
        by_payer = client.get(f"/api/admin/practitioner-service-prices?payer_id={data['payer'].id}", headers=headers(tenant_context))
        by_plan = client.get(f"/api/admin/practitioner-service-prices?payer_plan_id={data['plan'].id}", headers=headers(tenant_context))
        invalid_status = client.get("/api/admin/practitioner-service-prices?status=archived", headers=headers(tenant_context))
    finally:
        clear_overrides()
    assert all_prices.status_code == 200
    assert len(all_prices.json()["data"]) == 3
    assert {item["status"] for item in all_prices.json()["data"]} == {"active", "inactive"}
    assert len(active.json()["data"]) == 2
    assert len(inactive.json()["data"]) == 1
    assert len(include_inactive_false.json()["data"]) == 2
    expected_ids = {str(data["active_price"].id), str(data["inactive_price"].id)}
    for response in [by_org, by_practitioner, by_service, by_payer_type, by_payer, by_plan]:
        assert response.status_code == 200
        assert {item["id"] for item in response.json()["data"]} == expected_ids
        assert all(item["organization_name"] == "Clínica Vida" for item in response.json()["data"])
    assert invalid_status.status_code == 400
    assert invalid_status.json()["error"]["code"] == "VALIDATION_ERROR"


def test_get_practitioner_service_price_detail_returns_readable_data(admin_session, tenant_context, base_data):
    org, practitioner, service, payer_type, payer, plan = base_data
    price = PractitionerServicePrice(practitioner_service=service, payer_plan=plan, price=Decimal("100000.00"), currency="COP", valid_from=date(2026, 1, 1))
    admin_session.add(price)
    admin_session.flush()
    install_overrides(admin_session, tenant_context)
    try:
        response = TestClient(app).get(f"/api/admin/practitioner-service-prices/{price.id}", headers=headers(tenant_context))
    finally:
        clear_overrides()
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["id"] == str(price.id)
    assert_price_readable(data, service, org, practitioner, plan, payer, payer_type)


def test_patch_practitioner_service_price_editable_fields_and_reactivation(admin_session, tenant_context, base_data):
    _org, _practitioner, service, _payer_type, _payer, plan = base_data
    price = PractitionerServicePrice(practitioner_service=service, payer_plan=plan, price=Decimal("100000.00"), currency="COP", valid_from=date(2026, 1, 1), valid_to=date(2026, 1, 31))
    admin_session.add(price)
    admin_session.flush()
    install_overrides(admin_session, tenant_context)
    client = TestClient(app)
    try:
        patched = client.patch(
            f"/api/admin/practitioner-service-prices/{price.id}",
            json={"price": 120000, "currency": "USD", "valid_from": "2026-02-01", "valid_to": "2026-02-28"},
            headers=headers(tenant_context),
        )
        inactivated = client.patch(f"/api/admin/practitioner-service-prices/{price.id}", json={"status": "inactive"}, headers=headers(tenant_context))
        reactivated = client.patch(f"/api/admin/practitioner-service-prices/{price.id}", json={"status": "active"}, headers=headers(tenant_context))
        rejects_service = client.patch(f"/api/admin/practitioner-service-prices/{price.id}", json={"practitioner_service_id": str(uuid4())}, headers=headers(tenant_context))
        rejects_plan = client.patch(f"/api/admin/practitioner-service-prices/{price.id}", json={"payer_plan_id": str(uuid4())}, headers=headers(tenant_context))
    finally:
        clear_overrides()
    assert patched.status_code == 200
    assert patched.json()["data"]["price"] == 120000
    assert patched.json()["data"]["currency"] == "USD"
    assert patched.json()["data"]["valid_from"] == "2026-02-01"
    assert patched.json()["data"]["valid_to"] == "2026-02-28"
    assert inactivated.json()["data"]["status"] == "inactive"
    assert reactivated.json()["data"]["status"] == "active"
    assert rejects_service.status_code == 422
    assert rejects_service.json()["error"]["code"] == "VALIDATION_ERROR"
    assert rejects_plan.status_code == 422
    assert rejects_plan.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.parametrize("field", ["service", "plan", "payer", "payer_type"])
def test_patch_practitioner_service_price_reactivation_rejects_inactive_parents(admin_session, tenant_context, base_data, field):
    _org, _practitioner, service, payer_type, payer, plan = base_data
    price = PractitionerServicePrice(practitioner_service=service, payer_plan=plan, price=Decimal("100000.00"), currency="COP", valid_from=date(2026, 1, 1), status="inactive")
    admin_session.add(price)
    admin_session.flush()
    if field == "service":
        service.status = "inactive"
    elif field == "plan":
        plan.status = "inactive"
    elif field == "payer":
        payer.status = "inactive"
    else:
        payer_type.status = "inactive"
    admin_session.flush()
    install_overrides(admin_session, tenant_context)
    try:
        response = TestClient(app).patch(f"/api/admin/practitioner-service-prices/{price.id}", json={"status": "active"}, headers=headers(tenant_context))
    finally:
        clear_overrides()
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "BUSINESS_RULE_VIOLATION"


def test_disable_practitioner_service_price_keeps_historical_record(admin_session, tenant_context, base_data):
    _org, _practitioner, service, _payer_type, _payer, plan = base_data
    price = PractitionerServicePrice(practitioner_service=service, payer_plan=plan, price=Decimal("100000.00"), currency="COP", valid_from=date(2026, 1, 1))
    admin_session.add(price)
    admin_session.flush()
    install_overrides(admin_session, tenant_context)
    client = TestClient(app)
    try:
        disabled = client.post(f"/api/admin/practitioner-service-prices/{price.id}/disable", json={}, headers=headers(tenant_context))
        listed = client.get("/api/admin/practitioner-service-prices", headers=headers(tenant_context))
    finally:
        clear_overrides()
    assert disabled.status_code == 200
    assert disabled.json()["data"]["status"] == "inactive"
    assert any(item["id"] == str(price.id) and item["status"] == "inactive" for item in listed.json()["data"])


def test_list_prices_by_service_status_filter_and_readable_serialization(admin_session, tenant_context, base_data):
    org, practitioner, service, payer_type, payer, plan = base_data
    active_price = PractitionerServicePrice(practitioner_service=service, payer_plan=plan, price=Decimal("100000.00"), currency="COP", valid_from=date(2026, 1, 1), status="active")
    inactive_price = PractitionerServicePrice(practitioner_service=service, payer_plan=plan, price=Decimal("90000.00"), currency="COP", valid_from=date(2025, 1, 1), status="inactive")
    admin_session.add_all([active_price, inactive_price])
    admin_session.flush()
    install_overrides(admin_session, tenant_context)
    client = TestClient(app)
    try:
        all_prices = client.get(f"/api/admin/practitioner-services/{service.id}/prices", headers=headers(tenant_context))
        active = client.get(f"/api/admin/practitioner-services/{service.id}/prices?status=active", headers=headers(tenant_context))
        inactive = client.get(f"/api/admin/practitioner-services/{service.id}/prices?status=inactive", headers=headers(tenant_context))
        invalid_status = client.get(f"/api/admin/practitioner-services/{service.id}/prices?status=archived", headers=headers(tenant_context))
    finally:
        clear_overrides()
    assert len(all_prices.json()["data"]) == 2
    assert [item["id"] for item in active.json()["data"]] == [str(active_price.id)]
    assert [item["id"] for item in inactive.json()["data"]] == [str(inactive_price.id)]
    assert invalid_status.status_code == 400
    assert invalid_status.json()["error"]["code"] == "VALIDATION_ERROR"
    assert_price_readable(active.json()["data"][0], service, org, practitioner, plan, payer, payer_type)


def test_practitioner_service_price_duplicate_and_overlap_rules(admin_session, tenant_context, base_data):
    _org, _practitioner, service, _payer_type, _payer, plan = base_data
    install_overrides(admin_session, tenant_context)
    client = TestClient(app)
    try:
        first = client.post("/api/admin/practitioner-service-prices", json=price_payload(service, plan, valid_from="2026-01-01", valid_to="2026-01-31"), headers=headers(tenant_context))
        duplicate = client.post("/api/admin/practitioner-service-prices", json=price_payload(service, plan, valid_from="2026-01-01", valid_to="2026-01-15"), headers=headers(tenant_context))
        overlap = client.post("/api/admin/practitioner-service-prices", json=price_payload(service, plan, valid_from="2026-01-15", valid_to="2026-02-15"), headers=headers(tenant_context))
        non_overlap = client.post("/api/admin/practitioner-service-prices", json=price_payload(service, plan, valid_from="2026-02-01", valid_to="2026-02-28"), headers=headers(tenant_context))
        open_price = client.post("/api/admin/practitioner-service-prices", json=price_payload(service, plan, valid_from="2026-03-01", valid_to=None), headers=headers(tenant_context))
        open_overlap = client.post("/api/admin/practitioner-service-prices", json=price_payload(service, plan, valid_from="2026-04-01", valid_to=None), headers=headers(tenant_context))
        client.post(f"/api/admin/practitioner-service-prices/{open_price.json()['data']['id']}/disable", json={}, headers=headers(tenant_context))
        historical_overlap = client.post("/api/admin/practitioner-service-prices", json=price_payload(service, plan, valid_from="2026-04-01", valid_to=None), headers=headers(tenant_context))
    finally:
        clear_overrides()
    assert first.status_code == 200
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "CONFLICT"
    assert overlap.status_code == 409
    assert overlap.json()["error"]["code"] == "CONFLICT"
    assert non_overlap.status_code == 200
    assert open_price.status_code == 200
    assert open_overlap.status_code == 409
    assert open_overlap.json()["error"]["code"] == "CONFLICT"
    assert historical_overlap.status_code == 200
