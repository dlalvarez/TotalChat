from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.admin.dependencies import get_db_session
from app.auth.bootstrap import hash_password
from app.auth.jwt import create_access_token
from app.main import app
from app.models.public import Tenant, User, UserTenant
from app.models.tenant import Organization


@pytest.fixture()
def auth_session(monkeypatch):
    monkeypatch.setenv("TOTALCHAT_JWT_SECRET", "test-secret")
    from app.core.config import get_settings
    get_settings.cache_clear()
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    with engine.connect() as conn:
        conn.exec_driver_sql("ATTACH DATABASE ':memory:' AS public")
    for table in [Tenant.__table__, User.__table__, UserTenant.__table__, Organization.__table__]:
        table.create(engine)
    with Session(engine) as session:
        yield session
    get_settings.cache_clear()


def override_session(session):
    def _override():
        yield session
    app.dependency_overrides[get_db_session] = _override


def clear_overrides():
    app.dependency_overrides.clear()


def create_user_tenant(session, *, user_status="active", link_status="active", tenant_status="active", email="admin@example.com", password="secret"):
    tenant = Tenant(id=uuid4(), name="Clínica Demo", slug="clinica-demo", schema_name="tenant_clinica_demo", status=tenant_status)
    user = User(id=uuid4(), email=email, full_name="Admin", password_hash=hash_password(password), status=user_status)
    link = UserTenant(user_id=user.id, tenant_id=tenant.id, role="owner", status=link_status)
    session.add_all([tenant, user, link])
    session.commit()
    return user, tenant


def test_login_success(auth_session):
    create_user_tenant(auth_session)
    override_session(auth_session)
    try:
        response = TestClient(app).post("/api/auth/login", json={"email": "admin@example.com", "password": "secret"})
    finally:
        clear_overrides()
    assert response.status_code == 200
    assert response.json()["data"]["token_type"] == "bearer"
    assert response.json()["data"]["expires_in"] == 1800


def test_login_fails_bad_password(auth_session):
    create_user_tenant(auth_session)
    override_session(auth_session)
    try:
        response = TestClient(app).post("/api/auth/login", json={"email": "admin@example.com", "password": "bad"})
    finally:
        clear_overrides()
    assert response.status_code == 401


def test_login_fails_inactive_user(auth_session):
    create_user_tenant(auth_session, user_status="inactive")
    override_session(auth_session)
    try:
        response = TestClient(app).post("/api/auth/login", json={"email": "admin@example.com", "password": "secret"})
    finally:
        clear_overrides()
    assert response.status_code == 401


def test_login_fails_without_active_links(auth_session):
    create_user_tenant(auth_session, link_status="inactive")
    override_session(auth_session)
    try:
        response = TestClient(app).post("/api/auth/login", json={"email": "admin@example.com", "password": "secret"})
    finally:
        clear_overrides()
    assert response.status_code == 403


def test_me_returns_tenants_without_schema_name(auth_session):
    user, _tenant = create_user_tenant(auth_session)
    token, _ = create_access_token(user_id=user.id, email=user.email)
    override_session(auth_session)
    try:
        response = TestClient(app).get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    finally:
        clear_overrides()
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["email"] == "admin@example.com"
    assert data["tenants"][0]["tenant_name"] == "Clínica Demo"
    assert "schema_name" not in str(data)


def test_admin_route_requires_token(auth_session):
    _user, tenant = create_user_tenant(auth_session)
    override_session(auth_session)
    try:
        response = TestClient(app).get("/api/admin/organizations", headers={"X-TotalChat-Tenant-Id": str(tenant.id)})
    finally:
        clear_overrides()
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


def test_admin_route_rejects_unlinked_tenant(auth_session):
    user, _tenant = create_user_tenant(auth_session)
    other = Tenant(id=uuid4(), name="Otra", slug="otra", schema_name="tenant_otra", status="active")
    auth_session.add(other); auth_session.commit()
    token, _ = create_access_token(user_id=user.id, email=user.email)
    override_session(auth_session)
    try:
        response = TestClient(app).get("/api/admin/organizations", headers={"Authorization": f"Bearer {token}", "X-TotalChat-Tenant-Id": str(other.id)})
    finally:
        clear_overrides()
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "AUTHORIZATION_FAILED"


def test_admin_route_accepts_linked_tenant(auth_session):
    user, tenant = create_user_tenant(auth_session)
    token, _ = create_access_token(user_id=user.id, email=user.email)
    override_session(auth_session)
    try:
        response = TestClient(app).get("/api/admin/organizations", headers={"Authorization": f"Bearer {token}", "X-TotalChat-Tenant-Id": str(tenant.id)})
    finally:
        clear_overrides()
    assert response.status_code == 200


def test_invalid_token_fails(auth_session):
    _user, tenant = create_user_tenant(auth_session)
    override_session(auth_session)
    try:
        response = TestClient(app).get("/api/admin/organizations", headers={"Authorization": "Bearer bad.token.value", "X-TotalChat-Tenant-Id": str(tenant.id)})
    finally:
        clear_overrides()
    assert response.status_code == 401


def test_admin_route_still_requires_tenant_header(auth_session):
    user, _tenant = create_user_tenant(auth_session)
    token, _ = create_access_token(user_id=user.id, email=user.email)
    override_session(auth_session)
    try:
        response = TestClient(app).get("/api/admin/organizations", headers={"Authorization": f"Bearer {token}"})
    finally:
        clear_overrides()
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"
