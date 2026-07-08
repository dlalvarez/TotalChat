from datetime import date, datetime, time
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.admin.bookings import get_booking_scheduling_provider
from app.api.admin.dependencies import get_admin_tenant_context, get_db_session
from app.main import app
from app.models.tenant import (
    AvailabilityRule,
    Booking,
    Location,
    Organization,
    Patient,
    Payer,
    PayerPlan,
    PayerType,
    Practitioner,
    PractitionerService,
    PractitionerServicePrice,
    Room,
    ServiceModality,
)
from app.tenancy.context import TenantContext

TENANT_TABLES = [
    Organization.__table__, Location.__table__, Room.__table__, Practitioner.__table__, PractitionerService.__table__,
    ServiceModality.__table__, PayerType.__table__, Payer.__table__, PayerPlan.__table__, PractitionerServicePrice.__table__,
    Patient.__table__, AvailabilityRule.__table__, Booking.__table__,
]


@pytest.fixture()
def tenant_context():
    return TenantContext(tenant_id=uuid4(), slug="clinica-vida", schema_name="tenant_clinica_vida")


@pytest.fixture()
def booking_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    for table in TENANT_TABLES:
        table.create(engine)
    with Session(engine) as session:
        org = Organization(name="Clínica Vida", organization_type="clinic")
        loc = Location(organization=org, name="Sede Norte", address="Calle 123")
        room = Room(location=loc, name="Consultorio 301")
        practitioner = Practitioner(full_name="Dra. Ana Pérez", status="active")
        service = PractitionerService(organization=org, practitioner=practitioner, name="Consulta psicológica", duration_minutes=50, status="active")
        payer_type = PayerType(code="particular", name="Particular", status="active")
        payer = Payer(payer_type=payer_type, name="Particular", status="active")
        plan = PayerPlan(payer=payer, name="Tarifa particular", status="active")
        price = PractitionerServicePrice(practitioner_service=service, payer_plan=plan, price=Decimal("100000.00"), currency="COP", valid_from=date(2026, 1, 1), status="active")
        patient = Patient(full_name="Paciente Existente", phone="+573009990000", email="existente@example.com")
        session.add_all([org, loc, room, practitioner, service, payer_type, payer, plan, price, patient])
        session.flush()
        session.add(ServiceModality(practitioner_service_id=service.id, modality="in_person", location_id=loc.id, room_id=room.id, status="active"))
        session.add(AvailabilityRule(organization_id=org.id, practitioner_id=practitioner.id, practitioner_service_id=None, location_id=loc.id, room_id=room.id, modality="in_person", weekday=5, start_time=time(9), end_time=time(11), valid_from=date(2026, 7, 1), status="active"))
        session.flush()
        yield session, loc, room, practitioner, service, plan, price, patient


def clear_overrides() -> None:
    app.dependency_overrides.clear()


def install_overrides(session, tenant_context):
    def override_session():
        yield session

    app.dependency_overrides[get_db_session] = override_session
    app.dependency_overrides[get_admin_tenant_context] = lambda: tenant_context


def payload(loc, room, service, plan, *, patient=None, starts_at="2026-07-10T09:00:00-05:00"):
    return {
        "patient": patient or {"id": None, "full_name": "Juan Pérez", "phone": "+573001112233", "email": None},
        "practitioner_service_id": str(service.id),
        "payer_plan_id": str(plan.id),
        "modality": "in_person",
        "starts_at": starts_at,
        "location_id": str(loc.id),
        "room_id": str(room.id),
        "created_channel": "admin",
    }


def test_admin_bookings_create_tentative_booking_with_minimal_patient(booking_session, tenant_context):
    session, loc, room, _practitioner, service, plan, _price, _existing_patient = booking_session
    install_overrides(session, tenant_context)
    try:
        response = TestClient(app).post("/api/admin/bookings", json=payload(loc, room, service, plan), headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()

    assert response.status_code == 200
    body = response.json()
    assert list(body) == ["data"]
    data = body["data"]
    assert data["status"] == "tentative"
    assert data["payment_status"] == "pending"
    assert data["service_name_snapshot"] == "Consulta psicológica"
    assert data["payer_plan_name_snapshot"] == "Tarifa particular"
    assert data["price_snapshot"] == 100000
    assert data["currency_snapshot"] == "COP"
    assert data["total_amount"] == 100000
    assert "schema_name" not in data
    patient = session.get(Patient, UUID(data["patient_id"]))
    assert patient.full_name == "Juan Pérez"
    assert patient.profile_status == "minimal"
    assert patient.created_from_channel == "admin"


def test_admin_bookings_uses_existing_patient_when_id_is_provided(booking_session, tenant_context):
    session, loc, room, _practitioner, service, plan, _price, existing_patient = booking_session
    install_overrides(session, tenant_context)
    try:
        response = TestClient(app).post(
            "/api/admin/bookings",
            json=payload(loc, room, service, plan, patient={"id": str(existing_patient.id), "full_name": None, "phone": None, "email": None}, starts_at="2026-07-10T10:00:00-05:00"),
            headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)},
        )
    finally:
        clear_overrides()

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["patient_id"] == str(existing_patient.id)
    assert session.scalar(select(Patient).where(Patient.full_name == "Juan Pérez")) is None


def test_admin_bookings_missing_tenant_header_returns_authentication_required():
    response = TestClient(app).post("/api/admin/bookings", json={"patient": {"full_name": "Juan Pérez"}, "practitioner_service_id": str(uuid4()), "payer_plan_id": str(uuid4()), "modality": "in_person", "starts_at": "2026-07-10T09:00:00-05:00", "created_channel": "admin"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


def test_admin_bookings_slot_conflict_maps_to_slot_not_available(booking_session, tenant_context):
    session, loc, room, practitioner, service, plan, _price, existing_patient = booking_session
    session.add(Booking(
        organization_id=service.organization_id, patient_id=existing_patient.id, practitioner_id=practitioner.id,
        practitioner_service_id=service.id, payer_plan_id=plan.id, location_id=loc.id, room_id=room.id, modality="in_person",
        starts_at=datetime(2026, 7, 10, 9, 0), ends_at=datetime(2026, 7, 10, 9, 50), status="tentative",
        service_name_snapshot=service.name, duration_minutes_snapshot=service.duration_minutes, practitioner_name_snapshot=practitioner.full_name,
        modality_snapshot="in_person", payer_plan_name_snapshot=plan.name, price_snapshot=Decimal("100000.00"), currency_snapshot="COP", total_amount=Decimal("100000.00"),
    ))
    session.flush()
    install_overrides(session, tenant_context)
    try:
        response = TestClient(app).post("/api/admin/bookings", json=payload(loc, room, service, plan), headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SLOT_NOT_AVAILABLE"


def test_admin_bookings_missing_price_maps_to_resource_not_found(booking_session, tenant_context):
    session, loc, room, _practitioner, service, plan, price, _existing_patient = booking_session
    price.status = "inactive"
    session.flush()
    install_overrides(session, tenant_context)
    try:
        response = TestClient(app).post("/api/admin/bookings", json=payload(loc, room, service, plan), headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_admin_bookings_endpoint_delegates_to_booking_service_scheduling_provider(booking_session, tenant_context):
    session, loc, room, _practitioner, service, plan, _price, _existing_patient = booking_session
    captured = {"called": False}

    class RecordingProvider:
        def list_available_slots(self, session, tenant_context, **kwargs):
            return []

        def ensure_slot_available(self, session, **kwargs):
            captured["called"] = True
            captured["session"] = session
            captured["kwargs"] = kwargs

    install_overrides(session, tenant_context)
    app.dependency_overrides[get_booking_scheduling_provider] = lambda: RecordingProvider()
    try:
        response = TestClient(app).post("/api/admin/bookings", json=payload(loc, room, service, plan), headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()

    assert response.status_code == 200
    assert captured["called"] is True
    assert captured["session"] is session
    assert captured["kwargs"]["location_id"] == loc.id


def _create_booking_via_api(session, tenant_context, loc, room, service, plan, *, starts_at="2026-07-10T09:00:00-05:00", patient=None):
    install_overrides(session, tenant_context)
    try:
        response = TestClient(app).post(
            "/api/admin/bookings",
            json=payload(loc, room, service, plan, patient=patient, starts_at=starts_at),
            headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)},
        )
    finally:
        clear_overrides()
    assert response.status_code == 200
    return response.json()["data"]


def _direct_booking(session, loc, room, practitioner, service, plan, patient, *, starts_at, status="tentative"):
    booking = Booking(
        organization_id=service.organization_id,
        patient_id=patient.id,
        practitioner_id=practitioner.id,
        practitioner_service_id=service.id,
        payer_plan_id=plan.id,
        location_id=loc.id,
        room_id=room.id,
        modality="in_person",
        starts_at=starts_at,
        ends_at=starts_at.replace(hour=starts_at.hour + 1),
        status=status,
        service_name_snapshot=service.name,
        duration_minutes_snapshot=service.duration_minutes,
        practitioner_name_snapshot=practitioner.full_name,
        modality_snapshot="in_person",
        location_name_snapshot=loc.name,
        payer_plan_name_snapshot=plan.name,
        price_snapshot=Decimal("100000.00"),
        currency_snapshot="COP",
        total_amount=Decimal("100000.00"),
    )
    session.add(booking)
    session.flush()
    return booking


def test_admin_bookings_get_returns_created_booking(booking_session, tenant_context):
    session, loc, room, _practitioner, service, plan, _price, _existing_patient = booking_session
    created = _create_booking_via_api(session, tenant_context, loc, room, service, plan)
    install_overrides(session, tenant_context)
    try:
        response = TestClient(app).get(f"/api/admin/bookings/{created['id']}", headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["id"] == created["id"]
    assert data["starts_at"] is not None
    assert data["ends_at"] is not None
    assert data["modality"] == "in_person"
    assert data["practitioner_name_snapshot"] == "Dra. Ana Pérez"


def test_admin_bookings_get_does_not_expose_schema_name(booking_session, tenant_context):
    session, loc, room, _practitioner, service, plan, _price, _existing_patient = booking_session
    created = _create_booking_via_api(session, tenant_context, loc, room, service, plan)
    install_overrides(session, tenant_context)
    try:
        response = TestClient(app).get(f"/api/admin/bookings/{created['id']}", headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()

    assert response.status_code == 200
    assert "schema_name" not in response.json()["data"]


def test_admin_bookings_get_unknown_booking_returns_404(booking_session, tenant_context):
    session, *_ = booking_session
    install_overrides(session, tenant_context)
    try:
        response = TestClient(app).get(f"/api/admin/bookings/{uuid4()}", headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_admin_bookings_list_bookings(booking_session, tenant_context):
    session, loc, room, practitioner, service, plan, _price, existing_patient = booking_session
    booking = _direct_booking(session, loc, room, practitioner, service, plan, existing_patient, starts_at=datetime(2026, 7, 10, 9, 0))
    install_overrides(session, tenant_context)
    try:
        response = TestClient(app).get("/api/admin/bookings", headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()

    assert response.status_code == 200
    body = response.json()
    assert body["data"][0]["id"] == str(booking.id)
    assert body["meta"] == {"limit": 50, "offset": 0}


def test_admin_bookings_list_filters_by_status(booking_session, tenant_context):
    session, loc, room, practitioner, service, plan, _price, existing_patient = booking_session
    wanted = _direct_booking(session, loc, room, practitioner, service, plan, existing_patient, starts_at=datetime(2026, 7, 10, 9, 0), status="confirmed")
    _direct_booking(session, loc, room, practitioner, service, plan, existing_patient, starts_at=datetime(2026, 7, 11, 9, 0), status="tentative")
    install_overrides(session, tenant_context)
    try:
        response = TestClient(app).get("/api/admin/bookings?status=confirmed", headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()

    assert response.status_code == 200
    assert [item["id"] for item in response.json()["data"]] == [str(wanted.id)]


def test_admin_bookings_list_filters_by_practitioner_id(booking_session, tenant_context):
    session, loc, room, practitioner, service, plan, _price, existing_patient = booking_session
    wanted = _direct_booking(session, loc, room, practitioner, service, plan, existing_patient, starts_at=datetime(2026, 7, 10, 9, 0))
    other_practitioner = Practitioner(full_name="Dr. Otro", status="active")
    other_service = PractitionerService(organization_id=service.organization_id, practitioner=other_practitioner, name="Otra consulta", duration_minutes=50, status="active")
    session.add_all([other_practitioner, other_service]); session.flush()
    _direct_booking(session, loc, room, other_practitioner, other_service, plan, existing_patient, starts_at=datetime(2026, 7, 11, 9, 0))
    install_overrides(session, tenant_context)
    try:
        response = TestClient(app).get(f"/api/admin/bookings?practitioner_id={practitioner.id}", headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()

    assert response.status_code == 200
    assert [item["id"] for item in response.json()["data"]] == [str(wanted.id)]


def test_admin_bookings_list_filters_by_patient_id(booking_session, tenant_context):
    session, loc, room, practitioner, service, plan, _price, existing_patient = booking_session
    wanted = _direct_booking(session, loc, room, practitioner, service, plan, existing_patient, starts_at=datetime(2026, 7, 10, 9, 0))
    other_patient = Patient(full_name="Otro Paciente")
    session.add(other_patient); session.flush()
    _direct_booking(session, loc, room, practitioner, service, plan, other_patient, starts_at=datetime(2026, 7, 11, 9, 0))
    install_overrides(session, tenant_context)
    try:
        response = TestClient(app).get(f"/api/admin/bookings?patient_id={existing_patient.id}", headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()

    assert response.status_code == 200
    assert [item["id"] for item in response.json()["data"]] == [str(wanted.id)]


def test_admin_bookings_list_filters_by_date_range(booking_session, tenant_context):
    session, loc, room, practitioner, service, plan, _price, existing_patient = booking_session
    _direct_booking(session, loc, room, practitioner, service, plan, existing_patient, starts_at=datetime(2026, 7, 9, 9, 0))
    wanted = _direct_booking(session, loc, room, practitioner, service, plan, existing_patient, starts_at=datetime(2026, 7, 10, 9, 0))
    _direct_booking(session, loc, room, practitioner, service, plan, existing_patient, starts_at=datetime(2026, 7, 11, 9, 0))
    install_overrides(session, tenant_context)
    try:
        response = TestClient(app).get("/api/admin/bookings?date_from=2026-07-10&date_to=2026-07-10", headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()

    assert response.status_code == 200
    assert [item["id"] for item in response.json()["data"]] == [str(wanted.id)]


def test_admin_bookings_list_limit_offset_works(booking_session, tenant_context):
    session, loc, room, practitioner, service, plan, _price, existing_patient = booking_session
    _first = _direct_booking(session, loc, room, practitioner, service, plan, existing_patient, starts_at=datetime(2026, 7, 9, 9, 0))
    second = _direct_booking(session, loc, room, practitioner, service, plan, existing_patient, starts_at=datetime(2026, 7, 10, 9, 0))
    _third = _direct_booking(session, loc, room, practitioner, service, plan, existing_patient, starts_at=datetime(2026, 7, 11, 9, 0))
    install_overrides(session, tenant_context)
    try:
        response = TestClient(app).get("/api/admin/bookings?limit=1&offset=1", headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()

    assert response.status_code == 200
    assert [item["id"] for item in response.json()["data"]] == [str(second.id)]
    assert response.json()["meta"] == {"limit": 1, "offset": 1}


def test_admin_bookings_list_missing_tenant_header_returns_authentication_required():
    response = TestClient(app).get("/api/admin/bookings")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


def test_admin_bookings_cancel_from_tentative_preserves_reason(booking_session, tenant_context):
    session, loc, room, practitioner, service, plan, _price, patient = booking_session
    booking = _direct_booking(session, loc, room, practitioner, service, plan, patient, starts_at=datetime(2026, 7, 10, 9, 0), status="tentative")
    install_overrides(session, tenant_context)
    try:
        response = TestClient(app).post(f"/api/admin/bookings/{booking.id}/cancel", json={"reason": "Doctor unavailable", "release_slot": True}, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "cancelled_by_admin"
    assert response.json()["data"]["admin_cancellation_reason"] == "Doctor unavailable"
    assert "schema_name" not in response.json()["data"]


def test_admin_bookings_cancel_from_confirmed_without_payment(booking_session, tenant_context):
    session, loc, room, practitioner, service, plan, _price, patient = booking_session
    booking = _direct_booking(session, loc, room, practitioner, service, plan, patient, starts_at=datetime(2026, 7, 10, 9, 0), status="confirmed_without_payment")
    install_overrides(session, tenant_context)
    try:
        response = TestClient(app).post(f"/api/admin/bookings/{booking.id}/cancel", json={"reason": "Patient called admin"}, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "cancelled_by_admin"


def test_admin_bookings_cancel_from_terminal_state_fails_business_rule(booking_session, tenant_context):
    session, loc, room, practitioner, service, plan, _price, patient = booking_session
    booking = _direct_booking(session, loc, room, practitioner, service, plan, patient, starts_at=datetime(2026, 7, 10, 9, 0), status="cancelled_by_admin")
    install_overrides(session, tenant_context)
    try:
        response = TestClient(app).post(f"/api/admin/bookings/{booking.id}/cancel", json={"reason": "Again"}, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "BUSINESS_RULE_VIOLATION"


def test_admin_bookings_confirm_allowed_without_required_payment(booking_session, tenant_context):
    session, loc, room, practitioner, service, plan, _price, patient = booking_session
    service.requires_payment = False
    booking = _direct_booking(session, loc, room, practitioner, service, plan, patient, starts_at=datetime(2026, 7, 10, 9, 0), status="tentative")
    install_overrides(session, tenant_context)
    try:
        response = TestClient(app).post(f"/api/admin/bookings/{booking.id}/confirm", json={}, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "confirmed_without_payment"


def test_admin_bookings_confirm_from_cancelled_by_admin_fails_business_rule(booking_session, tenant_context):
    session, loc, room, practitioner, service, plan, _price, patient = booking_session
    service.requires_payment = False
    booking = _direct_booking(session, loc, room, practitioner, service, plan, patient, starts_at=datetime(2026, 7, 10, 9, 0), status="cancelled_by_admin")
    install_overrides(session, tenant_context)
    try:
        response = TestClient(app).post(f"/api/admin/bookings/{booking.id}/confirm", json={}, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "BUSINESS_RULE_VIOLATION"


def test_admin_bookings_action_requests_do_not_accept_schema_name(booking_session, tenant_context):
    session, loc, room, practitioner, service, plan, _price, patient = booking_session
    service.requires_payment = False
    booking = _direct_booking(session, loc, room, practitioner, service, plan, patient, starts_at=datetime(2026, 7, 10, 9, 0), status="tentative")
    install_overrides(session, tenant_context)
    try:
        confirm_response = TestClient(app).post(f"/api/admin/bookings/{booking.id}/confirm", json={"schema_name": "tenant_bad"}, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
        cancel_response = TestClient(app).post(f"/api/admin/bookings/{booking.id}/cancel", json={"reason": "x", "schema_name": "tenant_bad"}, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()
    assert confirm_response.status_code == 422
    assert cancel_response.status_code == 422


def test_admin_booking_actions_delegate_to_domain_service(monkeypatch, booking_session, tenant_context):
    session, loc, room, practitioner, service, plan, _price, patient = booking_session
    booking = _direct_booking(session, loc, room, practitioner, service, plan, patient, starts_at=datetime(2026, 7, 10, 9, 0), status="tentative")
    service.requires_payment = False
    called = {"confirm": False}
    from app.services.booking import BookingService
    original = BookingService.confirm_booking

    def recording_confirm(self, booking_id):
        called["confirm"] = True
        return original(self, booking_id)

    monkeypatch.setattr(BookingService, "confirm_booking", recording_confirm)
    install_overrides(session, tenant_context)
    try:
        response = TestClient(app).post(f"/api/admin/bookings/{booking.id}/confirm", json={}, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()
    assert response.status_code == 200
    assert called["confirm"] is True


def reschedule_payload(loc, room, *, starts_at="2026-07-10T10:00:00-05:00", reason="Solicitud paciente"):
    return {
        "new_starts_at": starts_at,
        "new_location_id": str(loc.id),
        "new_room_id": str(room.id),
        "reason": reason,
    }


def test_admin_bookings_reschedule_from_confirmed_updates_slot_location_room_and_reason(booking_session, tenant_context):
    session, loc, room, practitioner, service, plan, _price, patient = booking_session
    new_loc = Location(organization_id=service.organization_id, name="Sede Sur", address="Carrera 45")
    new_room = Room(location=new_loc, name="Consultorio 402")
    session.add_all([new_loc, new_room])
    session.flush()
    session.add(ServiceModality(practitioner_service_id=service.id, modality="in_person", location_id=new_loc.id, room_id=new_room.id, status="active"))
    booking = _direct_booking(session, loc, room, practitioner, service, plan, patient, starts_at=datetime(2026, 7, 10, 9, 0), status="confirmed")
    install_overrides(session, tenant_context)
    try:
        response = TestClient(app).post(f"/api/admin/bookings/{booking.id}/reschedule", json=reschedule_payload(new_loc, new_room, starts_at="2026-07-10T10:00:00-05:00"), headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "rescheduled"
    assert datetime.fromisoformat(data["starts_at"]).replace(tzinfo=None) == datetime(2026, 7, 10, 10, 0)
    assert datetime.fromisoformat(data["ends_at"]).replace(tzinfo=None) == datetime(2026, 7, 10, 10, 50)
    assert data["location_id"] == str(new_loc.id)
    assert data["room_id"] == str(new_room.id)
    assert data["admin_reschedule_reason"] == "Solicitud paciente"
    persisted = session.get(Booking, booking.id)
    assert persisted.location_id == new_loc.id
    assert persisted.room_id == new_room.id
    assert persisted.address_snapshot == "Carrera 45"
    assert persisted.room_snapshot == "Consultorio 402"
    assert persisted.admin_reschedule_reason == "Solicitud paciente"
    assert persisted.patient_id == patient.id
    assert persisted.practitioner_service_id == service.id
    assert persisted.payer_plan_id == plan.id
    assert persisted.price_snapshot == Decimal("100000.00")


def test_admin_bookings_reschedule_from_confirmed_without_payment(booking_session, tenant_context):
    session, loc, room, practitioner, service, plan, _price, patient = booking_session
    booking = _direct_booking(session, loc, room, practitioner, service, plan, patient, starts_at=datetime(2026, 7, 10, 9, 0), status="confirmed_without_payment")
    install_overrides(session, tenant_context)
    try:
        response = TestClient(app).post(f"/api/admin/bookings/{booking.id}/reschedule", json=reschedule_payload(loc, room), headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "rescheduled"


@pytest.mark.parametrize("status", ["tentative", "cancelled_by_admin"])
def test_admin_bookings_reschedule_invalid_states_fail_business_rule(booking_session, tenant_context, status):
    session, loc, room, practitioner, service, plan, _price, patient = booking_session
    booking = _direct_booking(session, loc, room, practitioner, service, plan, patient, starts_at=datetime(2026, 7, 10, 9, 0), status=status)
    install_overrides(session, tenant_context)
    try:
        response = TestClient(app).post(f"/api/admin/bookings/{booking.id}/reschedule", json=reschedule_payload(loc, room), headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "BUSINESS_RULE_VIOLATION"


def test_admin_bookings_reschedule_request_rejects_schema_name(booking_session, tenant_context):
    session, loc, room, practitioner, service, plan, _price, patient = booking_session
    booking = _direct_booking(session, loc, room, practitioner, service, plan, patient, starts_at=datetime(2026, 7, 10, 9, 0), status="confirmed")
    body = reschedule_payload(loc, room) | {"schema_name": "tenant_bad"}
    install_overrides(session, tenant_context)
    try:
        response = TestClient(app).post(f"/api/admin/bookings/{booking.id}/reschedule", json=body, headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()
    assert response.status_code == 422


def test_admin_bookings_reschedule_slot_conflict_is_rejected(booking_session, tenant_context):
    session, loc, room, practitioner, service, plan, _price, patient = booking_session
    booking = _direct_booking(session, loc, room, practitioner, service, plan, patient, starts_at=datetime(2026, 7, 10, 9, 0), status="confirmed")
    _direct_booking(session, loc, room, practitioner, service, plan, patient, starts_at=datetime(2026, 7, 10, 10, 0), status="confirmed")
    install_overrides(session, tenant_context)
    try:
        response = TestClient(app).post(f"/api/admin/bookings/{booking.id}/reschedule", json=reschedule_payload(loc, room), headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SLOT_NOT_AVAILABLE"


def test_admin_booking_reschedule_delegates_to_service_and_provider(monkeypatch, booking_session, tenant_context):
    session, loc, room, practitioner, service, plan, _price, patient = booking_session
    booking = _direct_booking(session, loc, room, practitioner, service, plan, patient, starts_at=datetime(2026, 7, 10, 9, 0), status="confirmed")
    called = {"service": False, "provider": False}
    from app.services.booking import BookingService
    original = BookingService.reschedule_booking_by_admin

    def recording_reschedule(self, *args, **kwargs):
        called["service"] = True
        return original(self, *args, **kwargs)

    class RecordingProvider:
        def list_available_slots(self, session, tenant_context, **kwargs):
            return []

        def ensure_slot_available(self, session, **kwargs):
            called["provider"] = True

    monkeypatch.setattr(BookingService, "reschedule_booking_by_admin", recording_reschedule)
    install_overrides(session, tenant_context)
    app.dependency_overrides[get_booking_scheduling_provider] = lambda: RecordingProvider()
    try:
        response = TestClient(app).post(f"/api/admin/bookings/{booking.id}/reschedule", json=reschedule_payload(loc, room), headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()
    assert response.status_code == 200
    assert called == {"service": True, "provider": True}


def test_admin_bookings_reschedule_same_slot_excludes_current_booking(booking_session, tenant_context):
    session, loc, room, practitioner, service, plan, _price, patient = booking_session
    booking = _direct_booking(session, loc, room, practitioner, service, plan, patient, starts_at=datetime(2026, 7, 10, 9, 0), status="confirmed")
    install_overrides(session, tenant_context)
    try:
        response = TestClient(app).post(
            f"/api/admin/bookings/{booking.id}/reschedule",
            json=reschedule_payload(loc, room, starts_at="2026-07-10T09:00:00-05:00"),
            headers={"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)},
        )
    finally:
        clear_overrides()
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "rescheduled"
