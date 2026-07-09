from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.admin.dependencies import get_admin_tenant_context, get_db_session
from app.main import app
from app.models.tenant import Booking, Location, Organization, Patient, PaymentAttempt, PaymentEvidence, PaymentReview, PaymentSettings, Practitioner, PractitionerService, Room
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
def session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    for table in TENANT_TABLES:
        table.create(engine)
    with Session(engine) as db:
        yield db


@pytest.fixture()
def booking(session):
    org = Organization(name="Clínica Vida", organization_type="clinic")
    practitioner = Practitioner(full_name="Dra. Ana")
    patient = Patient(full_name="Juan Pérez")
    session.add_all([org, practitioner, patient])
    session.flush()
    service = PractitionerService(organization_id=org.id, practitioner_id=practitioner.id, name="Consulta", duration_minutes=30)
    location = Location(organization_id=org.id, name="Sede")
    session.add_all([service, location])
    session.flush()
    room = Room(location_id=location.id, name="101")
    session.add(room)
    session.flush()
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
        status="pending_payment_evidence",
        payment_status="pending",
        service_name_snapshot="Consulta",
        duration_minutes_snapshot=30,
        practitioner_name_snapshot="Dra. Ana",
        modality_snapshot="in_person",
        location_name_snapshot="Sede",
        price_snapshot=Decimal("100.00"),
        currency_snapshot="COP",
        total_amount=Decimal("100.00"),
        room_snapshot="101",
    )
    session.add(item)
    session.commit()
    return item


@pytest.fixture(autouse=True)
def clear_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


def request(method, path, session, tenant_context, *, json=None):
    def override_session():
        yield session

    app.dependency_overrides[get_db_session] = override_session
    app.dependency_overrides[get_admin_tenant_context] = lambda: tenant_context
    return TestClient(app).request(method, path, json=json, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})


def add_settings(session, booking, *, missing=False, overdue=False, deadline=60):
    settings = PaymentSettings(
        organization_id=booking.organization_id,
        manual_review_deadline_minutes=deadline,
        release_slot_on_missing_evidence=missing,
        release_slot_on_review_overdue=overdue,
        status="active",
    )
    session.add(settings)
    session.commit()
    return settings


def add_attempt(session, booking, *, method="transfer", status="evidence_required", expires_delta=-5, evidence_delta=-120):
    attempt = PaymentAttempt(
        booking_id=booking.id,
        method=method,
        amount=Decimal("100.00"),
        currency="COP",
        status=status,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=expires_delta),
        evidence_received_at=datetime.now(timezone.utc) + timedelta(minutes=evidence_delta) if status == "evidence_received" else None,
    )
    session.add(attempt)
    session.commit()
    return attempt


def test_expire_missing_evidence_success_sets_expired_and_preserves_audit(session, tenant_context, booking):
    add_settings(session, booking, missing=False)
    attempt = add_attempt(session, booking)
    response = request("POST", f"/api/internal/payment-attempts/{attempt.id}/expire-missing-evidence", session, tenant_context, json={})
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["payment_attempt"]["status"] == "expired"
    assert data["action"] == "expired_missing_evidence"
    assert data["booking_action"] == "not_applied_policy_disabled"
    assert "schema_name" not in str(data)
    session.refresh(attempt)
    session.refresh(booking)
    assert attempt.status == "expired"
    assert booking.status == "pending_payment_evidence"
    assert session.scalars(select(PaymentEvidence)).all() == []
    assert session.scalars(select(PaymentReview)).all() == []
    assert attempt.reviewed_at is None and attempt.reviewed_by_user_id is None


@pytest.mark.parametrize("method", ["simulated", "pay_on_site"])
def test_expire_rejects_non_transfer_attempts(session, tenant_context, booking, method):
    add_settings(session, booking)
    attempt = add_attempt(session, booking, method=method)
    response = request("POST", f"/api/internal/payment-attempts/{attempt.id}/expire-missing-evidence", session, tenant_context, json={})
    assert response.status_code == 409


def test_expire_rejects_unknown_wrong_status_and_not_expired_without_force(session, tenant_context, booking):
    add_settings(session, booking)
    unknown = request("POST", f"/api/internal/payment-attempts/{uuid4()}/expire-missing-evidence", session, tenant_context, json={})
    wrong = add_attempt(session, booking, status="evidence_received")
    wrong_response = request("POST", f"/api/internal/payment-attempts/{wrong.id}/expire-missing-evidence", session, tenant_context, json={})
    future = add_attempt(session, booking, expires_delta=30)
    future_response = request("POST", f"/api/internal/payment-attempts/{future.id}/expire-missing-evidence", session, tenant_context, json={})
    force_response = request("POST", f"/api/internal/payment-attempts/{future.id}/expire-missing-evidence", session, tenant_context, json={"force": True})
    assert unknown.status_code == 404
    assert wrong_response.status_code == 409
    assert future_response.status_code == 409
    assert force_response.status_code == 200


def test_expire_with_release_policy_uses_safe_transition_when_available(session, tenant_context, booking):
    add_settings(session, booking, missing=True)
    attempt = add_attempt(session, booking)
    response = request("POST", f"/api/internal/payment-attempts/{attempt.id}/expire-missing-evidence", session, tenant_context, json={"notes": "deadline"})
    assert response.status_code == 200
    assert response.json()["data"]["booking_action"] == "released_via_booking_transition_service"
    session.refresh(booking)
    assert booking.status == "expired_no_evidence"


def test_review_overdue_success_preserves_status_evidence_and_reviews(session, tenant_context, booking):
    booking.status = "pending_manual_payment_review"
    add_settings(session, booking, overdue=False, deadline=60)
    attempt = add_attempt(session, booking, status="evidence_received", evidence_delta=-120)
    evidence = PaymentEvidence(payment_attempt_id=attempt.id, uploaded_at=attempt.evidence_received_at, notes="receipt")
    session.add(evidence)
    session.commit()
    response = request("POST", f"/api/internal/payment-attempts/{attempt.id}/mark-review-overdue", session, tenant_context, json={})
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["action"] == "marked_review_overdue"
    assert data["payment_attempt"]["status"] == "evidence_received"
    assert data["booking_action"] == "not_applied_policy_disabled"
    assert "schema_name" not in str(data)
    session.refresh(attempt)
    session.refresh(booking)
    assert attempt.status == "evidence_received"
    assert attempt.reviewed_at is None and attempt.reviewed_by_user_id is None
    assert session.get(PaymentEvidence, evidence.id) is not None
    assert session.scalars(select(PaymentReview)).all() == []
    assert booking.status == "pending_manual_payment_review"


@pytest.mark.parametrize("method", ["simulated", "pay_on_site"])
def test_review_overdue_rejects_non_transfer_attempts(session, tenant_context, booking, method):
    add_settings(session, booking)
    attempt = add_attempt(session, booking, method=method, status="evidence_received")
    response = request("POST", f"/api/internal/payment-attempts/{attempt.id}/mark-review-overdue", session, tenant_context, json={})
    assert response.status_code == 409


def test_review_overdue_rejects_unknown_wrong_status_and_not_due_without_force(session, tenant_context, booking):
    add_settings(session, booking, deadline=60)
    unknown = request("POST", f"/api/internal/payment-attempts/{uuid4()}/mark-review-overdue", session, tenant_context, json={})
    wrong = add_attempt(session, booking, status="evidence_required")
    wrong_response = request("POST", f"/api/internal/payment-attempts/{wrong.id}/mark-review-overdue", session, tenant_context, json={})
    early = add_attempt(session, booking, status="evidence_received", evidence_delta=-10)
    early_response = request("POST", f"/api/internal/payment-attempts/{early.id}/mark-review-overdue", session, tenant_context, json={})
    force_response = request("POST", f"/api/internal/payment-attempts/{early.id}/mark-review-overdue", session, tenant_context, json={"force": True})
    assert unknown.status_code == 404
    assert wrong_response.status_code == 409
    assert early_response.status_code == 409
    assert force_response.status_code == 200


def test_review_overdue_release_policy_does_not_bypass_unsafe_booking_transition(session, tenant_context, booking):
    booking.status = "tentative"
    add_settings(session, booking, overdue=True, deadline=60)
    attempt = add_attempt(session, booking, status="evidence_received", evidence_delta=-120)
    response = request("POST", f"/api/internal/payment-attempts/{attempt.id}/mark-review-overdue", session, tenant_context, json={})
    assert response.status_code == 200
    assert response.json()["data"]["booking_action"] == "not_applied_no_safe_domain_transition"
    session.refresh(booking)
    assert booking.status == "tentative"


def test_internal_payload_rejects_schema_name(session, tenant_context, booking):
    add_settings(session, booking)
    attempt = add_attempt(session, booking)
    response = request("POST", f"/api/internal/payment-attempts/{attempt.id}/expire-missing-evidence", session, tenant_context, json={"schema_name": "tenant_x"})
    assert response.status_code == 422
