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
from app.models.tenant import Booking, Location, Organization, Patient, PaymentAttempt, PaymentEvidence, PaymentReview, PaymentSettings, Practitioner, PractitionerService, Room
from app.tenancy.context import TenantContext

TABLES = [Organization.__table__, Location.__table__, Room.__table__, Practitioner.__table__, PractitionerService.__table__, Patient.__table__, Booking.__table__, PaymentSettings.__table__, PaymentAttempt.__table__, PaymentEvidence.__table__, PaymentReview.__table__]

@pytest.fixture()
def tenant_context(): return TenantContext(tenant_id=uuid4(), slug="clinica-vida", schema_name="tenant_clinica_vida")

@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    for table in TABLES: table.create(engine)
    with Session(engine) as s: yield s

@pytest.fixture()
def seed(session):
    org = Organization(name="Clínica Vida", organization_type="clinic")
    other_org = Organization(name="Clínica Norte", organization_type="clinic")
    practitioner = Practitioner(full_name="Dra. Ana")
    other_practitioner = Practitioner(full_name="Dr. Carlos")
    patient = Patient(full_name="Juan Pérez", document_number="12345", phone="+573001112233")
    other_patient = Patient(full_name="María Gómez", document_number="67890")
    session.add_all([org, other_org, practitioner, other_practitioner, patient, other_patient]); session.flush()
    service = PractitionerService(organization_id=org.id, practitioner_id=practitioner.id, name="Consulta", duration_minutes=30, requires_payment=True)
    other_service = PractitionerService(organization_id=other_org.id, practitioner_id=other_practitioner.id, name="Terapia", duration_minutes=45, requires_payment=True)
    location = Location(organization_id=org.id, name="Sede Principal")
    other_location = Location(organization_id=other_org.id, name="Sede Norte")
    session.add_all([service, other_service, location, other_location]); session.flush()
    room = Room(location_id=location.id, name="101")
    other_room = Room(location_id=other_location.id, name="202")
    session.add_all([room, other_room]); session.flush()
    starts_at = datetime(2026, 7, 20, 9, 0, tzinfo=timezone.utc)
    other_starts_at = datetime(2026, 7, 22, 10, 0, tzinfo=timezone.utc)
    booking = Booking(organization_id=org.id, patient_id=patient.id, practitioner_id=practitioner.id, practitioner_service_id=service.id, location_id=location.id, room_id=room.id, modality="in_person", starts_at=starts_at, ends_at=starts_at + timedelta(minutes=30), status="tentative", payment_status="pending", service_name_snapshot=service.name, duration_minutes_snapshot=30, practitioner_name_snapshot=practitioner.full_name, modality_snapshot="in_person", location_name_snapshot=location.name, price_snapshot=Decimal("100000.00"), currency_snapshot="COP", total_amount=Decimal("100000.00"), room_snapshot=room.name)
    other_booking = Booking(organization_id=other_org.id, patient_id=other_patient.id, practitioner_id=other_practitioner.id, practitioner_service_id=other_service.id, location_id=other_location.id, room_id=other_room.id, modality="in_person", starts_at=other_starts_at, ends_at=other_starts_at + timedelta(minutes=45), status="tentative", payment_status="pending", service_name_snapshot=other_service.name, duration_minutes_snapshot=45, practitioner_name_snapshot=other_practitioner.full_name, modality_snapshot="in_person", location_name_snapshot=other_location.name, price_snapshot=Decimal("80000.00"), currency_snapshot="COP", total_amount=Decimal("80000.00"), room_snapshot=other_room.name)
    session.add_all([booking, other_booking]); session.commit()
    return {"org": org, "other_org": other_org, "practitioner": practitioner, "other_practitioner": other_practitioner, "patient": patient, "booking": booking, "other_booking": other_booking, "location": location, "room": room, "service": service}

def req(method, path, session, tenant_context, json=None):
    def override_session(): yield session
    app.dependency_overrides[get_db_session] = override_session
    app.dependency_overrides[get_admin_tenant_context] = lambda: tenant_context
    try: return TestClient(app).request(method, path, json=json, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally: app.dependency_overrides.clear()

def create_attempt(session, booking, *, method="transfer", status="evidence_received", amount="100000.00", evidence=True):
    attempt = PaymentAttempt(booking_id=booking.id, method=method, amount=Decimal(amount), currency="COP", status=status, evidence_received_at=datetime.now(timezone.utc) if status == "evidence_received" else None)
    session.add(attempt); session.flush()
    if evidence:
        session.add(PaymentEvidence(payment_attempt_id=attempt.id, storage_object_key="tenant/evidence/receipt.png", original_filename="receipt.png", content_type="image/png", uploaded_at=datetime.now(timezone.utc), uploaded_channel="admin", notes="Legible"))
    session.commit(); return attempt

def review_payload(**overrides):
    data = {"reviewer_user_id": str(uuid4()), "notes": "Validado por admin"}; data.update(overrides); return data

def assert_no_schema(payload): assert "schema_name" not in str(payload)

def test_get_payments_lists_readable_booking_context(session, tenant_context, seed):
    attempt = create_attempt(session, seed["booking"])
    response = req("GET", "/api/admin/payments", session, tenant_context)
    assert response.status_code == 200, response.text
    data = response.json()["data"][0]
    assert data["id"] == str(attempt.id)
    assert data["booking_id"] == str(seed["booking"].id)
    assert data["patient_name"] == "Juan Pérez"
    assert data["practitioner_name"] == "Dra. Ana"
    assert data["practitioner_service_name"] == "Consulta"
    assert data["organization_name"] == "Clínica Vida"
    assert data["location_name"] == "Sede Principal"
    assert data["room_name"] == "101"
    assert data["evidence_count"] == 1
    assert_no_schema(data)


def test_get_payment_detail_includes_evidence_and_reviews(session, tenant_context, seed):
    attempt = create_attempt(session, seed["booking"])
    session.add(PaymentReview(payment_attempt_id=attempt.id, decision="approved", reviewer_user_id=uuid4(), reviewed_at=datetime.now(timezone.utc), notes="ok")); session.commit()
    response = req("GET", f"/api/admin/payments/{attempt.id}", session, tenant_context)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["evidence"][0]["original_filename"] == "receipt.png"
    assert data["reviews"][0]["decision"] == "approved"
    assert data["latest_review_decision"] == "approved"
    assert_no_schema(data)


@pytest.mark.parametrize("query", ["organization_id={org}", "method=transfer", "status=evidence_received", "date_from=2026-07-20", "date_to=2026-07-20", "patient=Juan", "patient=12345", "practitioner_id={practitioner}", "booking_id={booking}"])
def test_get_payments_filters(session, tenant_context, seed, query):
    expected = create_attempt(session, seed["booking"])
    create_attempt(session, seed["other_booking"], amount="80000.00")
    rendered = query.format(org=seed["org"].id, practitioner=seed["practitioner"].id, booking=seed["booking"].id)
    response = req("GET", f"/api/admin/payments?{rendered}", session, tenant_context)
    assert response.status_code == 200, response.text
    ids = [item["id"] for item in response.json()["data"]]
    assert str(expected.id) in ids
    if rendered not in {"method=transfer", "status=evidence_received"}:
        assert ids == [str(expected.id)]


def test_approve_transfer_evidence_received_uses_domain_service(session, tenant_context, seed):
    reviewer_id = uuid4(); attempt = create_attempt(session, seed["booking"])
    response = req("POST", f"/api/admin/payments/{attempt.id}/approve", session, tenant_context, json=review_payload(reviewer_user_id=str(reviewer_id)))
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    stored_attempt = session.get(PaymentAttempt, attempt.id); booking = session.get(Booking, seed["booking"].id)
    review = session.scalars(select(PaymentReview).where(PaymentReview.payment_attempt_id == attempt.id)).one()
    assert data["status"] == "approved"
    assert stored_attempt.status == "approved" and stored_attempt.reviewed_at is not None and stored_attempt.reviewed_by_user_id == reviewer_id
    assert review.decision == "approved" and review.reviewer_user_id == reviewer_id
    assert booking.payment_status == "paid" and booking.status == "tentative"


def test_reject_transfer_evidence_received_requires_notes_and_preserves_booking_evidence(session, tenant_context, seed):
    reviewer_id = uuid4(); attempt = create_attempt(session, seed["booking"])
    before_evidence_ids = [row.id for row in session.scalars(select(PaymentEvidence)).all()]
    missing = req("POST", f"/api/admin/payments/{attempt.id}/reject", session, tenant_context, json={})
    assert missing.status_code == 422
    response = req("POST", f"/api/admin/payments/{attempt.id}/reject", session, tenant_context, json={"reviewer_user_id": str(reviewer_id), "reason": "No corresponde al monto"})
    assert response.status_code == 200, response.text
    stored_attempt = session.get(PaymentAttempt, attempt.id); booking = session.get(Booking, seed["booking"].id)
    review = session.scalars(select(PaymentReview).where(PaymentReview.payment_attempt_id == attempt.id)).one()
    assert stored_attempt.status == "rejected" and stored_attempt.reviewed_at is not None and stored_attempt.reviewed_by_user_id == reviewer_id
    assert review.decision == "rejected" and review.notes == "No corresponde al monto"
    assert booking.payment_status == "rejected" and booking.status == "tentative"
    assert [row.id for row in session.scalars(select(PaymentEvidence)).all()] == before_evidence_ids


@pytest.mark.parametrize("method", ["pay_on_site", "simulated"])
@pytest.mark.parametrize("action", ["approve", "reject"])
def test_review_rejects_non_transfer_methods(session, tenant_context, seed, method, action):
    status = "pending" if method == "pay_on_site" else "simulated_approved"
    attempt = create_attempt(session, seed["booking"], method=method, status=status, evidence=False)
    response = req("POST", f"/api/admin/payments/{attempt.id}/{action}", session, tenant_context, json=review_payload())
    assert response.status_code == 409


@pytest.mark.parametrize("status", ["pending", "evidence_required", "approved", "rejected", "expired", "cancelled", "simulated_approved", "under_review"])
@pytest.mark.parametrize("action", ["approve", "reject"])
def test_review_rejects_non_reviewable_statuses(session, tenant_context, seed, status, action):
    attempt = create_attempt(session, seed["booking"], status=status, evidence=False)
    response = req("POST", f"/api/admin/payments/{attempt.id}/{action}", session, tenant_context, json=review_payload())
    assert response.status_code == 409


def test_old_payment_attempt_review_endpoints_sync_booking_payment_status(session, tenant_context, seed):
    approve_attempt = create_attempt(session, seed["booking"])
    approve_response = req("POST", f"/api/admin/payment-attempts/{approve_attempt.id}/approve", session, tenant_context, json=review_payload())
    assert approve_response.status_code == 200
    assert session.get(Booking, seed["booking"].id).payment_status == "paid"
    other_booking = seed["other_booking"]
    reject_attempt = create_attempt(session, other_booking)
    reject_response = req("POST", f"/api/admin/payment-attempts/{reject_attempt.id}/reject", session, tenant_context, json=review_payload(notes="No válido"))
    assert reject_response.status_code == 200
    assert session.get(Booking, other_booking.id).payment_status == "rejected"
