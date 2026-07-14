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
def review_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    for table in TENANT_TABLES:
        table.create(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture()
def booking(review_session):
    org = Organization(name="Clínica Vida", organization_type="clinic")
    practitioner = Practitioner(full_name="Dra. Ana")
    patient = Patient(full_name="Juan Pérez", phone="+573001112233")
    review_session.add_all([org, practitioner, patient])
    review_session.flush()
    service = PractitionerService(
        organization_id=org.id,
        practitioner_id=practitioner.id,
        name="Consulta",
        duration_minutes=30,
        requires_payment=True,
    )
    location = Location(organization_id=org.id, name="Sede Principal")
    review_session.add_all([service, location])
    review_session.flush()
    room = Room(location_id=location.id, name="101")
    review_session.add(room)
    review_session.flush()
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
    review_session.add(item)
    review_session.commit()
    return item


def clear_overrides():
    app.dependency_overrides.clear()


def request(method, path, session, tenant_context, *, json=None):
    def override_session():
        yield session

    app.dependency_overrides[get_db_session] = override_session
    app.dependency_overrides[get_admin_tenant_context] = lambda: tenant_context
    try:
        return TestClient(app).request(
            method,
            path,
            json=json,
            headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)},
        )
    finally:
        clear_overrides()


def create_attempt(session, booking, *, status="evidence_received", method="transfer", with_evidence=True):
    attempt = PaymentAttempt(
        booking_id=booking.id,
        method=method,
        amount=Decimal("100000.00"),
        currency="COP",
        status=status,
    )
    session.add(attempt)
    session.flush()
    if with_evidence:
        session.add(
            PaymentEvidence(
                payment_attempt_id=attempt.id,
                storage_object_key="tenant/evidence/receipt.png",
                original_filename="receipt.png",
                content_type="image/png",
                uploaded_at=datetime.now(timezone.utc),
                uploaded_channel="admin",
            )
        )
    session.commit()
    return attempt


def review_payload(**overrides):
    data = {"reviewer_user_id": str(uuid4()), "notes": "Validado por admin"}
    data.update(overrides)
    return data


@pytest.mark.parametrize("action,decision", [("approve", "approved"), ("reject", "rejected")])
def test_post_review_creates_payment_review(review_session, tenant_context, booking, action, decision):
    attempt = create_attempt(review_session, booking)
    response = request(
        "POST",
        f"/api/admin/payment-attempts/{attempt.id}/{action}",
        review_session,
        tenant_context,
        json=review_payload(),
    )
    assert response.status_code == 200
    assert response.json()["data"]["review"]["decision"] == decision
    stored_review = review_session.scalars(select(PaymentReview).where(PaymentReview.decision == decision)).one()
    assert stored_review.payment_attempt_id == attempt.id


@pytest.mark.parametrize("action,decision", [("approve", "approved"), ("reject", "rejected")])
def test_post_review_moves_attempt_status_and_sets_review_fields(review_session, tenant_context, booking, action, decision):
    reviewer_id = uuid4()
    attempt = create_attempt(review_session, booking)
    response = request(
        "POST",
        f"/api/admin/payment-attempts/{attempt.id}/{action}",
        review_session,
        tenant_context,
        json={"reviewer_user_id": str(reviewer_id), "notes": "ok"},
    )
    data = response.json()["data"]["payment_attempt"]
    stored = review_session.get(PaymentAttempt, attempt.id)
    assert data["status"] == decision
    assert data["reviewed_at"] is not None
    assert data["reviewed_by_user_id"] == str(reviewer_id)
    assert stored.status == decision
    assert stored.reviewed_at is not None
    assert stored.reviewed_by_user_id == reviewer_id
    assert review_session.get(Booking, booking.id).payment_status == ("paid" if decision == "approved" else "rejected")


@pytest.mark.parametrize("action", ["approve", "reject"])
def test_post_review_rejects_unknown_payment_attempt_id(review_session, tenant_context, action):
    response = request(
        "POST",
        f"/api/admin/payment-attempts/{uuid4()}/{action}",
        review_session,
        tenant_context,
        json=review_payload(),
    )
    assert response.status_code == 404


@pytest.mark.parametrize("action", ["approve", "reject"])
def test_post_review_rejects_schema_name(review_session, tenant_context, booking, action):
    attempt = create_attempt(review_session, booking)
    response = request(
        "POST",
        f"/api/admin/payment-attempts/{attempt.id}/{action}",
        review_session,
        tenant_context,
        json=review_payload(schema_name="tenant_x"),
    )
    assert response.status_code == 422


@pytest.mark.parametrize("action", ["approve", "reject"])
@pytest.mark.parametrize("status", ["pending", "evidence_required", "approved", "rejected", "cancelled", "expired", "simulated_approved"])
def test_post_review_rejects_attempts_without_evidence_received(review_session, tenant_context, booking, action, status):
    attempt = create_attempt(review_session, booking, status=status, with_evidence=False)
    response = request(
        "POST",
        f"/api/admin/payment-attempts/{attempt.id}/{action}",
        review_session,
        tenant_context,
        json=review_payload(),
    )
    assert response.status_code == 409


def test_post_approve_does_not_create_payment_evidence_call_gateway_or_confirm_booking(review_session, tenant_context, booking):
    attempt = create_attempt(review_session, booking, with_evidence=False)
    before_evidence_count = len(review_session.scalars(select(PaymentEvidence)).all())
    response = request(
        "POST",
        f"/api/admin/payment-attempts/{attempt.id}/approve",
        review_session,
        tenant_context,
        json=review_payload(),
    )
    assert response.status_code == 200
    assert len(review_session.scalars(select(PaymentEvidence)).all()) == before_evidence_count
    assert review_session.get(Booking, booking.id).status == "tentative"


def test_post_reject_does_not_delete_evidence_cancel_or_release_booking(review_session, tenant_context, booking):
    attempt = create_attempt(review_session, booking, with_evidence=True)
    before_evidence_ids = [row.id for row in review_session.scalars(select(PaymentEvidence)).all()]
    response = request(
        "POST",
        f"/api/admin/payment-attempts/{attempt.id}/reject",
        review_session,
        tenant_context,
        json=review_payload(),
    )
    assert response.status_code == 200
    assert [row.id for row in review_session.scalars(select(PaymentEvidence)).all()] == before_evidence_ids
    assert review_session.get(Booking, booking.id).status == "tentative"


def test_get_payment_reviews_lists_and_filters(review_session, tenant_context, booking):
    first = create_attempt(review_session, booking)
    second = create_attempt(review_session, booking)
    request("POST", f"/api/admin/payment-attempts/{first.id}/approve", review_session, tenant_context, json=review_payload(notes="first"))
    request("POST", f"/api/admin/payment-attempts/{second.id}/reject", review_session, tenant_context, json=review_payload(notes="second"))
    listed = request("GET", "/api/admin/payment-reviews", review_session, tenant_context)
    by_attempt = request("GET", f"/api/admin/payment-reviews?payment_attempt_id={first.id}", review_session, tenant_context)
    by_decision = request("GET", "/api/admin/payment-reviews?decision=rejected", review_session, tenant_context)
    assert listed.status_code == 200 and len(listed.json()["data"]) == 2
    assert [item["payment_attempt_id"] for item in by_attempt.json()["data"]] == [str(first.id)]
    assert [item["decision"] for item in by_decision.json()["data"]] == ["rejected"]


def test_get_payment_reviews_rejects_invalid_decision(review_session, tenant_context):
    response = request("GET", "/api/admin/payment-reviews?decision=pending", review_session, tenant_context)
    assert response.status_code == 400


def test_responses_do_not_expose_schema_name(review_session, tenant_context, booking):
    attempt = create_attempt(review_session, booking)
    approve = request(
        "POST",
        f"/api/admin/payment-attempts/{attempt.id}/approve",
        review_session,
        tenant_context,
        json=review_payload(),
    )
    reviews = request("GET", "/api/admin/payment-reviews", review_session, tenant_context)
    assert "schema_name" not in approve.text
    assert "schema_name" not in reviews.text
    assert UUID(approve.json()["data"]["review"]["id"])
