from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.admin.dependencies import get_admin_tenant_context, get_db_session
from app.auth.bootstrap import hash_password
from app.auth.jwt import create_access_token
from app.main import app
from app.models.public import Tenant, User, UserTenant
from app.models.tenant import Booking, Location, Organization, Patient, PaymentAttempt, Practitioner, PractitionerService
from app.tenancy.context import TenantContext

TENANT_TABLES = [Organization.__table__, Location.__table__, Practitioner.__table__, PractitionerService.__table__, Patient.__table__, Booking.__table__, PaymentAttempt.__table__]
PUBLIC_TABLES = [Tenant.__table__, User.__table__, UserTenant.__table__]


@pytest.fixture()
def dashboard_session(monkeypatch):
    monkeypatch.setenv("TOTALCHAT_JWT_SECRET", "test-secret")
    from app.core.config import get_settings
    get_settings.cache_clear()
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    with engine.connect() as conn:
        conn.exec_driver_sql("ATTACH DATABASE ':memory:' AS public")
    for table in PUBLIC_TABLES + TENANT_TABLES:
        table.create(engine)
    with Session(engine) as session:
        yield session
    get_settings.cache_clear()


@pytest.fixture()
def tenant_context():
    return TenantContext(tenant_id=uuid4(), slug="clinica-demo", schema_name="tenant_clinica_demo")


def override_session(session):
    def _override():
        yield session
    app.dependency_overrides[get_db_session] = _override


def clear_overrides():
    app.dependency_overrides.clear()


def req(session, tenant_context, *, headers=None):
    override_session(session)
    app.dependency_overrides[get_admin_tenant_context] = lambda: tenant_context
    try:
        return TestClient(app).get("/api/admin/dashboard/summary", headers=headers or {"X-TotalChat-Tenant-Id": str(tenant_context.tenant_id)})
    finally:
        clear_overrides()


def auth_req(session, tenant, user, *, include_token=True, include_tenant=True):
    token, _ = create_access_token(user_id=user.id, email=user.email)
    headers = {}
    if include_token:
        headers["Authorization"] = f"Bearer {token}"
    if include_tenant:
        headers["X-TotalChat-Tenant-Id"] = str(tenant.id)
    override_session(session)
    try:
        return TestClient(app).get("/api/admin/dashboard/summary", headers=headers)
    finally:
        clear_overrides()


def create_admin_user(session):
    tenant = Tenant(id=uuid4(), name="Clínica Demo", slug="clinica-demo", schema_name="tenant_clinica_demo", status="active")
    user = User(id=uuid4(), email="admin@example.com", full_name="Admin", password_hash=hash_password("secret"), status="active")
    link = UserTenant(user_id=user.id, tenant_id=tenant.id, role="owner", status="active")
    session.add_all([tenant, user, link]); session.commit()
    return tenant, user


def seed_dashboard(session, *, now: datetime):
    org = Organization(name="Clínica Vida", organization_type="clinic")
    practitioner = Practitioner(full_name="Dra. Ana", status="active")
    inactive_practitioner = Practitioner(full_name="Dr. Inactivo", status="inactive")
    patient = Patient(full_name="Paciente Uno")
    session.add_all([org, practitioner, inactive_practitioner, patient]); session.flush()
    service = PractitionerService(organization_id=org.id, practitioner_id=practitioner.id, name="Consulta", duration_minutes=30, requires_payment=True, status="active")
    inactive_service = PractitionerService(organization_id=org.id, practitioner_id=practitioner.id, name="Control inactivo", duration_minutes=30, requires_payment=True, status="inactive")
    location = Location(organization_id=org.id, name="Sede Principal", is_virtual=False)
    virtual_location = Location(organization_id=org.id, name="Teleconsulta", is_virtual=True)
    session.add_all([service, inactive_service, location, virtual_location]); session.flush()

    today = now.replace(hour=15, minute=0, second=0, microsecond=0)
    earlier_today = now.replace(hour=8, minute=0, second=0, microsecond=0)
    future = now + timedelta(days=1)
    virtual_without_link = now + timedelta(days=2)
    virtual_with_link = now + timedelta(days=3)
    yesterday = now - timedelta(days=1)

    bookings = [
        Booking(organization_id=org.id, patient_id=patient.id, practitioner_id=practitioner.id, practitioner_service_id=service.id, location_id=location.id, modality="in_person", starts_at=today, ends_at=today + timedelta(minutes=30), status="scheduled", payment_status="pending", service_name_snapshot="Consulta", duration_minutes_snapshot=30, practitioner_name_snapshot="Dra. Ana", modality_snapshot="in_person", location_name_snapshot="Sede Principal", price_snapshot=Decimal("100000"), currency_snapshot="COP", total_amount=Decimal("100000")),
        Booking(organization_id=org.id, patient_id=patient.id, practitioner_id=practitioner.id, practitioner_service_id=service.id, location_id=location.id, modality="in_person", starts_at=earlier_today, ends_at=earlier_today + timedelta(minutes=30), status="scheduled", payment_status="pending", service_name_snapshot="Consulta", duration_minutes_snapshot=30, practitioner_name_snapshot="Dra. Ana", modality_snapshot="in_person", location_name_snapshot="Sede Principal", price_snapshot=Decimal("100000"), currency_snapshot="COP", total_amount=Decimal("100000")),
        Booking(organization_id=org.id, patient_id=patient.id, practitioner_id=practitioner.id, practitioner_service_id=service.id, location_id=location.id, modality="in_person", starts_at=future, ends_at=future + timedelta(minutes=30), status="scheduled", payment_status="paid", service_name_snapshot="Consulta", duration_minutes_snapshot=30, practitioner_name_snapshot="Dra. Ana", modality_snapshot="in_person", location_name_snapshot="Sede Principal", price_snapshot=Decimal("100000"), currency_snapshot="COP", total_amount=Decimal("100000")),
        Booking(organization_id=org.id, patient_id=patient.id, practitioner_id=practitioner.id, practitioner_service_id=service.id, location_id=virtual_location.id, modality="virtual", starts_at=virtual_without_link, ends_at=virtual_without_link + timedelta(minutes=30), status="scheduled", payment_status="pending", service_name_snapshot="Consulta", duration_minutes_snapshot=30, practitioner_name_snapshot="Dra. Ana", modality_snapshot="virtual", location_name_snapshot="Teleconsulta", price_snapshot=Decimal("100000"), currency_snapshot="COP", total_amount=Decimal("100000")),
        Booking(organization_id=org.id, patient_id=patient.id, practitioner_id=practitioner.id, practitioner_service_id=service.id, location_id=virtual_location.id, modality="virtual", starts_at=virtual_with_link, ends_at=virtual_with_link + timedelta(minutes=30), status="scheduled", payment_status="pending", service_name_snapshot="Consulta", duration_minutes_snapshot=30, practitioner_name_snapshot="Dra. Ana", modality_snapshot="virtual", location_name_snapshot="Teleconsulta", price_snapshot=Decimal("100000"), currency_snapshot="COP", total_amount=Decimal("100000"), virtual_meeting_url="https://meet.example/abc"),
        Booking(organization_id=org.id, patient_id=patient.id, practitioner_id=practitioner.id, practitioner_service_id=service.id, location_id=location.id, modality="in_person", starts_at=yesterday, ends_at=yesterday + timedelta(minutes=30), status="scheduled", payment_status="pending", service_name_snapshot="Consulta", duration_minutes_snapshot=30, practitioner_name_snapshot="Dra. Ana", modality_snapshot="in_person", location_name_snapshot="Sede Principal", price_snapshot=Decimal("100000"), currency_snapshot="COP", total_amount=Decimal("100000")),
    ]
    session.add_all(bookings); session.flush()
    reviewable = PaymentAttempt(booking_id=bookings[0].id, method="transfer", amount=Decimal("100000"), currency="COP", status="evidence_received", evidence_received_at=now)
    ignored_method = PaymentAttempt(booking_id=bookings[0].id, method="simulated", amount=Decimal("100000"), currency="COP", status="evidence_received", evidence_received_at=now)
    ignored_status = PaymentAttempt(booking_id=bookings[0].id, method="transfer", amount=Decimal("100000"), currency="COP", status="approved", evidence_received_at=now)
    session.add_all([reviewable, ignored_method, ignored_status]); session.commit()
    return {"today": bookings[0], "reviewable": reviewable, "virtual_without_link": bookings[3]}


def test_endpoint_exige_auth(dashboard_session):
    tenant, user = create_admin_user(dashboard_session)
    response = auth_req(dashboard_session, tenant, user, include_token=False)
    assert response.status_code == 401


def test_endpoint_exige_tenant(dashboard_session):
    tenant, user = create_admin_user(dashboard_session)
    response = auth_req(dashboard_session, tenant, user, include_tenant=False)
    assert response.status_code == 401


def test_dashboard_summary_metrics_lists_and_no_schema_name(dashboard_session, tenant_context, monkeypatch):
    fixed_now = datetime(2026, 7, 17, 12, 0, tzinfo=timezone.utc)
    seed = seed_dashboard(dashboard_session, now=fixed_now)
    import app.api.admin.dashboard as dashboard_module
    monkeypatch.setattr(dashboard_module, "_now", lambda: fixed_now)

    response = req(dashboard_session, tenant_context)
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["metrics"] == {
        "appointments_today": 2,
        "upcoming_appointments": 5,
        "appointments_pending_payment": 5,
        "payment_reviews_pending": 1,
        "virtual_appointments_without_link": 1,
        "active_services": 1,
        "active_practitioners": 1,
    }
    assert [item["id"] for item in data["today_appointments"]] == [str(seed["today"].id)]
    assert data["pending_payment_reviews"] == [{
        "id": str(seed["reviewable"].id),
        "booking_id": str(seed["today"].id),
        "patient_name": "Paciente Uno",
        "practitioner_name": "Dra. Ana",
        "service_name": "Consulta",
        "amount": 100000.0,
        "currency": "COP",
        "evidence_received_at": fixed_now.isoformat(),
    }]
    assert [item["id"] for item in data["virtual_link_alerts"]] == [str(seed["virtual_without_link"].id)]
    assert "schema_name" not in str(data)


def test_metrics_use_current_tenant_context_session(tenant_context, monkeypatch):
    fixed_now = datetime(2026, 7, 17, 12, 0, tzinfo=timezone.utc)
    import app.api.admin.dashboard as dashboard_module
    monkeypatch.setattr(dashboard_module, "_now", lambda: fixed_now)

    def make_session(with_data: bool):
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        for table in TENANT_TABLES:
            table.create(engine)
        session = Session(engine)
        if with_data:
            seed_dashboard(session, now=fixed_now)
        return session

    empty_session = make_session(False)
    populated_session = make_session(True)
    try:
        assert req(empty_session, tenant_context).json()["data"]["metrics"]["appointments_today"] == 0
        assert req(populated_session, tenant_context).json()["data"]["metrics"]["appointments_today"] == 2
    finally:
        empty_session.close(); populated_session.close()
