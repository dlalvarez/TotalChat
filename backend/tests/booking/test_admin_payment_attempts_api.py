from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.admin.dependencies import get_admin_tenant_context, get_db_session
from app.main import app
from app.models.tenant import (
    Booking,
    Location,
    Organization,
    Patient,
    PaymentAttempt,
    PaymentEvidence,
    PaymentReview,
    PaymentSettings,
    Practitioner,
    PractitionerService,
    Room,
)
from app.tenancy.context import TenantContext

TENANT_TABLES = [
    Organization.__table__,
    Location.__table__,
    Room.__table__,
    Practitioner.__table__,
    PractitionerService.__table__,
    Patient.__table__,
    Booking.__table__,
    PaymentSettings.__table__,
    PaymentAttempt.__table__,
    PaymentEvidence.__table__,
    PaymentReview.__table__,
]


@pytest.fixture()
def tenant_context():
    return TenantContext(tenant_id=uuid4(), slug="clinica-vida", schema_name="tenant_clinica_vida")


@pytest.fixture()
def payment_attempt_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    for table in TENANT_TABLES:
        table.create(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture()
def booking(payment_attempt_session):
    org = Organization(name="Clínica Vida", organization_type="clinic")
    practitioner = Practitioner(full_name="Dra. Ana")
    patient = Patient(full_name="Juan Pérez", phone="+573001112233")
    payment_attempt_session.add_all([org, practitioner, patient])
    payment_attempt_session.flush()
    service = PractitionerService(
        organization_id=org.id,
        practitioner_id=practitioner.id,
        name="Consulta",
        duration_minutes=30,
        requires_payment=True,
    )
    location = Location(organization_id=org.id, name="Sede Principal")
    payment_attempt_session.add_all([service, location])
    payment_attempt_session.flush()
    room = Room(location_id=location.id, name="101")
    payment_attempt_session.add(room)
    payment_attempt_session.flush()
    starts_at = datetime.now(timezone.utc) + timedelta(days=1)
    item = Booking(
        organization_id=org.id,
        patient_id=patient.id,
        practitioner_id=practitioner.id,
        practitioner_service_id=service.id,
        location_id=location.id,
        room_id=room.id,
        modality="in_person",
        starts_at=starts_at,
        ends_at=starts_at + timedelta(minutes=30),
        status="tentative",
        payment_status="pending",
        service_name_snapshot=service.name,
        duration_minutes_snapshot=30,
        practitioner_name_snapshot=practitioner.full_name,
        modality_snapshot="in_person",
        location_name_snapshot=location.name,
        price_snapshot=Decimal("100000.00"),
        currency_snapshot="COP",
        total_amount=Decimal("100000.00"),
        room_snapshot=room.name,
    )
    payment_attempt_session.add(item)
    payment_attempt_session.commit()
    return item


def clear_overrides() -> None:
    app.dependency_overrides.clear()


def install_overrides(session, tenant_context, include_tenant=True):
    def override_session():
        yield session

    app.dependency_overrides[get_db_session] = override_session
    if include_tenant:
        app.dependency_overrides[get_admin_tenant_context] = lambda: tenant_context


def request(method, path, session, tenant_context, *, json=None, include_tenant=True):
    install_overrides(session, tenant_context, include_tenant=include_tenant)
    headers = {"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)} if include_tenant else None
    try:
        return TestClient(app).request(method, path, json=json, headers=headers)
    finally:
        clear_overrides()


def payload(booking, **overrides):
    data = {"booking_id": str(booking.id), "method": "transfer", "amount": "100000.00", "currency": "COP"}
    data.update(overrides)
    return data


def test_post_creates_transfer_payment_attempt_with_evidence_required(payment_attempt_session, tenant_context, booking):
    response = request("POST", "/api/admin/payment-attempts", payment_attempt_session, tenant_context, json=payload(booking))
    assert response.status_code == 200
    data = response.json()["data"]
    assert UUID(data["id"])
    assert data["booking_id"] == str(booking.id)
    assert data["method"] == "transfer"
    assert data["status"] == "evidence_required"


def test_post_creates_simulated_payment_attempt_with_simulated_approved(payment_attempt_session, tenant_context, booking):
    response = request("POST", "/api/admin/payment-attempts", payment_attempt_session, tenant_context, json=payload(booking, method="simulated"))
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "simulated_approved"


def test_post_creates_pay_on_site_payment_attempt_with_pending(payment_attempt_session, tenant_context, booking):
    response = request("POST", "/api/admin/payment-attempts", payment_attempt_session, tenant_context, json=payload(booking, method="pay_on_site"))
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "pending"


def test_post_rejects_missing_tenant_header(payment_attempt_session, tenant_context, booking):
    response = request("POST", "/api/admin/payment-attempts", payment_attempt_session, tenant_context, json=payload(booking), include_tenant=False)
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


def test_post_rejects_schema_name(payment_attempt_session, tenant_context, booking):
    response = request("POST", "/api/admin/payment-attempts", payment_attempt_session, tenant_context, json=payload(booking, schema_name="tenant_x"))
    assert response.status_code == 422


def test_post_rejects_unknown_booking_id(payment_attempt_session, tenant_context, booking):
    unknown_booking_id = str(uuid4())
    data = {
        "booking_id": unknown_booking_id,
        "method": "transfer",
        "amount": "100000.00",
        "currency": "COP",
    }
    response = request(
        "POST", "/api/admin/payment-attempts", payment_attempt_session, tenant_context,
        json=data,
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


@pytest.mark.parametrize("method", ["card", "manual_transfer", ""])
def test_post_rejects_invalid_method(payment_attempt_session, tenant_context, booking, method):
    response = request("POST", "/api/admin/payment-attempts", payment_attempt_session, tenant_context, json=payload(booking, method=method))
    assert response.status_code == 422


def test_post_rejects_negative_amount(payment_attempt_session, tenant_context, booking):
    response = request("POST", "/api/admin/payment-attempts", payment_attempt_session, tenant_context, json=payload(booking, amount="-1.00"))
    assert response.status_code == 422


@pytest.mark.parametrize("currency", ["cop", "CO", "COP1"])
def test_post_rejects_invalid_currency(payment_attempt_session, tenant_context, booking, currency):
    response = request("POST", "/api/admin/payment-attempts", payment_attempt_session, tenant_context, json=payload(booking, currency=currency))
    assert response.status_code == 422


def test_post_does_not_create_payment_evidence(payment_attempt_session, tenant_context, booking):
    request("POST", "/api/admin/payment-attempts", payment_attempt_session, tenant_context, json=payload(booking))
    assert payment_attempt_session.scalars(select(PaymentEvidence)).all() == []


def test_post_does_not_create_payment_review(payment_attempt_session, tenant_context, booking):
    request("POST", "/api/admin/payment-attempts", payment_attempt_session, tenant_context, json=payload(booking))
    assert payment_attempt_session.scalars(select(PaymentReview)).all() == []


def test_post_response_does_not_expose_schema_name(payment_attempt_session, tenant_context, booking):
    response = request("POST", "/api/admin/payment-attempts", payment_attempt_session, tenant_context, json=payload(booking))
    assert "schema_name" not in response.json()["data"]


def create_attempt(session, tenant_context, booking, method):
    return request("POST", "/api/admin/payment-attempts", session, tenant_context, json=payload(booking, method=method)).json()["data"]


def test_get_lists_payment_attempts(payment_attempt_session, tenant_context, booking):
    created = create_attempt(payment_attempt_session, tenant_context, booking, "transfer")
    response = request("GET", "/api/admin/payment-attempts", payment_attempt_session, tenant_context)
    assert response.status_code == 200
    assert [item["id"] for item in response.json()["data"]] == [created["id"]]


def test_get_filters_by_booking_id(payment_attempt_session, tenant_context, booking):
    create_attempt(payment_attempt_session, tenant_context, booking, "transfer")
    response = request("GET", f"/api/admin/payment-attempts?booking_id={booking.id}", payment_attempt_session, tenant_context)
    assert response.status_code == 200
    assert len(response.json()["data"]) == 1
    assert response.json()["data"][0]["booking_id"] == str(booking.id)


def test_get_filters_by_method(payment_attempt_session, tenant_context, booking):
    create_attempt(payment_attempt_session, tenant_context, booking, "transfer")
    create_attempt(payment_attempt_session, tenant_context, booking, "simulated")
    response = request("GET", "/api/admin/payment-attempts?method=simulated", payment_attempt_session, tenant_context)
    assert [item["method"] for item in response.json()["data"]] == ["simulated"]


def test_get_filters_by_status(payment_attempt_session, tenant_context, booking):
    create_attempt(payment_attempt_session, tenant_context, booking, "transfer")
    create_attempt(payment_attempt_session, tenant_context, booking, "simulated")
    response = request("GET", "/api/admin/payment-attempts?status=evidence_required", payment_attempt_session, tenant_context)
    assert [item["status"] for item in response.json()["data"]] == ["evidence_required"]


@pytest.mark.parametrize("query", ["method=card", "status=bank_confirmed"])
def test_get_rejects_invalid_method_status_filters(payment_attempt_session, tenant_context, booking, query):
    response = request("GET", f"/api/admin/payment-attempts?{query}", payment_attempt_session, tenant_context)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
