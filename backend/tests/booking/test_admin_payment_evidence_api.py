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
    Organization.__table__, Location.__table__, Room.__table__, Practitioner.__table__,
    PractitionerService.__table__, Patient.__table__, Booking.__table__, PaymentSettings.__table__,
    PaymentAttempt.__table__, PaymentEvidence.__table__, PaymentReview.__table__,
]


@pytest.fixture()
def tenant_context():
    return TenantContext(tenant_id=uuid4(), slug="clinica-vida", schema_name="tenant_clinica_vida")


@pytest.fixture()
def payment_evidence_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    for table in TENANT_TABLES:
        table.create(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture()
def booking(payment_evidence_session):
    org = Organization(name="Clínica Vida", organization_type="clinic")
    practitioner = Practitioner(full_name="Dra. Ana")
    patient = Patient(full_name="Juan Pérez", phone="+573001112233")
    payment_evidence_session.add_all([org, practitioner, patient])
    payment_evidence_session.flush()
    service = PractitionerService(organization_id=org.id, practitioner_id=practitioner.id, name="Consulta", duration_minutes=30, requires_payment=True)
    location = Location(organization_id=org.id, name="Sede Principal")
    payment_evidence_session.add_all([service, location])
    payment_evidence_session.flush()
    room = Room(location_id=location.id, name="101")
    payment_evidence_session.add(room)
    payment_evidence_session.flush()
    starts_at = datetime.now(timezone.utc) + timedelta(days=1)
    item = Booking(
        organization_id=org.id, patient_id=patient.id, practitioner_id=practitioner.id,
        practitioner_service_id=service.id, location_id=location.id, room_id=room.id,
        modality="in_person", starts_at=starts_at, ends_at=starts_at + timedelta(minutes=30),
        status="tentative", payment_status="pending", service_name_snapshot=service.name,
        duration_minutes_snapshot=30, practitioner_name_snapshot=practitioner.full_name,
        modality_snapshot="in_person", location_name_snapshot=location.name,
        price_snapshot=Decimal("100000.00"), currency_snapshot="COP", total_amount=Decimal("100000.00"),
        room_snapshot=room.name,
    )
    payment_evidence_session.add(item)
    payment_evidence_session.commit()
    return item


def clear_overrides():
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


def create_attempt(session, booking, method="transfer", status=None):
    attempt = PaymentAttempt(booking_id=booking.id, method=method, amount=Decimal("100000.00"), currency="COP", status=status or ("evidence_required" if method == "transfer" else "pending"))
    session.add(attempt)
    session.commit()
    return attempt


def payload(**overrides):
    data = {"storage_object_key": "tenant/evidence/receipt-1.png", "original_filename": "receipt.png", "content_type": "image/png", "uploaded_channel": "admin", "notes": "Paciente envió comprobante"}
    data.update(overrides)
    return data


def test_post_creates_evidence_for_transfer_attempt_in_evidence_required(payment_evidence_session, tenant_context, booking):
    attempt = create_attempt(payment_evidence_session, booking)
    response = request("POST", f"/api/admin/payment-attempts/{attempt.id}/evidence", payment_evidence_session, tenant_context, json=payload())
    assert response.status_code == 200
    evidence = response.json()["data"]["evidence"]
    assert UUID(evidence["id"])
    assert evidence["payment_attempt_id"] == str(attempt.id)
    assert evidence["storage_object_key"] == "tenant/evidence/receipt-1.png"


def test_post_moves_attempt_status_to_evidence_received(payment_evidence_session, tenant_context, booking):
    attempt = create_attempt(payment_evidence_session, booking)
    response = request("POST", f"/api/admin/payment-attempts/{attempt.id}/evidence", payment_evidence_session, tenant_context, json=payload())
    assert response.json()["data"]["payment_attempt"]["status"] == "evidence_received"
    assert payment_evidence_session.get(PaymentAttempt, attempt.id).status == "evidence_received"


def test_post_sets_evidence_received_at(payment_evidence_session, tenant_context, booking):
    attempt = create_attempt(payment_evidence_session, booking)
    response = request("POST", f"/api/admin/payment-attempts/{attempt.id}/evidence", payment_evidence_session, tenant_context, json=payload())
    assert response.json()["data"]["payment_attempt"]["evidence_received_at"] is not None


def test_post_rejects_missing_tenant_header(payment_evidence_session, tenant_context, booking):
    attempt = create_attempt(payment_evidence_session, booking)
    response = request("POST", f"/api/admin/payment-attempts/{attempt.id}/evidence", payment_evidence_session, tenant_context, json=payload(), include_tenant=False)
    assert response.status_code == 401


def test_post_rejects_schema_name(payment_evidence_session, tenant_context, booking):
    attempt = create_attempt(payment_evidence_session, booking)
    response = request("POST", f"/api/admin/payment-attempts/{attempt.id}/evidence", payment_evidence_session, tenant_context, json=payload(schema_name="tenant_x"))
    assert response.status_code == 422


def test_post_rejects_unknown_payment_attempt_id(payment_evidence_session, tenant_context):
    response = request("POST", f"/api/admin/payment-attempts/{uuid4()}/evidence", payment_evidence_session, tenant_context, json=payload())
    assert response.status_code == 404


@pytest.mark.parametrize("method", ["simulated", "pay_on_site"])
def test_post_rejects_non_transfer_payment_attempts(payment_evidence_session, tenant_context, booking, method):
    attempt = create_attempt(payment_evidence_session, booking, method=method)
    response = request("POST", f"/api/admin/payment-attempts/{attempt.id}/evidence", payment_evidence_session, tenant_context, json=payload())
    assert response.status_code == 409


@pytest.mark.parametrize("status", ["approved", "rejected", "cancelled", "expired"])
def test_post_rejects_terminal_transfer_attempt_statuses(payment_evidence_session, tenant_context, booking, status):
    attempt = create_attempt(payment_evidence_session, booking, status=status)
    response = request("POST", f"/api/admin/payment-attempts/{attempt.id}/evidence", payment_evidence_session, tenant_context, json=payload())
    assert response.status_code == 409


def test_post_does_not_create_payment_review(payment_evidence_session, tenant_context, booking):
    attempt = create_attempt(payment_evidence_session, booking)
    request("POST", f"/api/admin/payment-attempts/{attempt.id}/evidence", payment_evidence_session, tenant_context, json=payload())
    assert payment_evidence_session.scalars(select(PaymentReview)).all() == []


def test_post_does_not_approve_payment(payment_evidence_session, tenant_context, booking):
    attempt = create_attempt(payment_evidence_session, booking)
    request("POST", f"/api/admin/payment-attempts/{attempt.id}/evidence", payment_evidence_session, tenant_context, json=payload())
    assert payment_evidence_session.get(PaymentAttempt, attempt.id).status != "approved"


def test_post_does_not_confirm_booking(payment_evidence_session, tenant_context, booking):
    attempt = create_attempt(payment_evidence_session, booking)
    request("POST", f"/api/admin/payment-attempts/{attempt.id}/evidence", payment_evidence_session, tenant_context, json=payload())
    assert payment_evidence_session.get(Booking, booking.id).status == "tentative"


def test_response_does_not_expose_schema_name(payment_evidence_session, tenant_context, booking):
    attempt = create_attempt(payment_evidence_session, booking)
    response = request("POST", f"/api/admin/payment-attempts/{attempt.id}/evidence", payment_evidence_session, tenant_context, json=payload())
    assert "schema_name" not in response.text


def test_get_lists_evidence_by_payment_attempt_id(payment_evidence_session, tenant_context, booking):
    attempt = create_attempt(payment_evidence_session, booking)
    first = request("POST", f"/api/admin/payment-attempts/{attempt.id}/evidence", payment_evidence_session, tenant_context, json=payload(notes="first")).json()["data"]["evidence"]
    response = request("GET", f"/api/admin/payment-attempts/{attempt.id}/evidence", payment_evidence_session, tenant_context)
    assert response.status_code == 200
    assert [item["id"] for item in response.json()["data"]] == [first["id"]]
