from datetime import datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.admin.dependencies import get_admin_tenant_context, get_db_session
from app.main import app
from app.models.tenant import AvailabilityException, Location, Organization, Practitioner, Room
from app.tenancy.context import TenantContext

TABLES = [Organization.__table__, Location.__table__, Room.__table__, Practitioner.__table__, AvailabilityException.__table__]

@pytest.fixture()
def tenant_context(): return TenantContext(tenant_id=uuid4(), slug="clinica", schema_name="tenant_clinica")

@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    for table in TABLES: table.create(engine)
    with Session(engine) as s: yield s

@pytest.fixture()
def seed(session):
    org=Organization(name="Clínica Vida", organization_type="clinic"); loc=Location(organization_id=org.id, name="Sede Norte"); practitioner=Practitioner(full_name="Dra. Ana")
    session.add_all([org, practitioner]); session.flush(); loc.organization_id=org.id; session.add(loc); session.flush(); room=Room(location_id=loc.id, name="Consultorio 1"); session.add(room); session.commit()
    return {"org":org,"loc":loc,"room":room,"practitioner":practitioner}

def install(s, tc):
    def override_session(): yield s
    app.dependency_overrides[get_db_session] = override_session
    app.dependency_overrides[get_admin_tenant_context] = lambda: tc

def clear(): app.dependency_overrides.clear()
def request(method, path, s, tc, payload=None):
    install(s, tc)
    try: return getattr(TestClient(app), method)(path, json=payload, headers={"X-TotalChat-Tenant-Id": str(tc.tenant_id)}) if payload is not None else getattr(TestClient(app), method)(path, headers={"X-TotalChat-Tenant-Id": str(tc.tenant_id)})
    finally: clear()

def payload(seed, **kw):
    data={"practitioner_id":str(seed["practitioner"].id),"location_id":None,"room_id":None,"starts_at":"2026-07-20T10:00:00","ends_at":"2026-07-20T11:00:00","exception_type":"meeting","reason":"Comité"}
    data.update(kw); return data

def test_create_list_detail_patch_disable_reactivate_no_schema(session, tenant_context, seed):
    created=request('post','/api/admin/availability-exceptions',session,tenant_context,payload(seed)); assert created.status_code==200, created.text
    data=created.json()['data']; assert data['practitioner_name']=='Dra. Ana'; assert data['exception_type_label']=='Reunión'; assert 'schema_name' not in data
    listing=request('get','/api/admin/availability-exceptions',session,tenant_context).json()['data']; assert len(listing)==1 and listing[0]['practitioner_name']=='Dra. Ana'
    detail=request('get',f"/api/admin/availability-exceptions/{data['id']}",session,tenant_context); assert detail.status_code==200
    patched=request('patch',f"/api/admin/availability-exceptions/{data['id']}",session,tenant_context,{"exception_type":"training","reason":"Curso","starts_at":"2026-07-20T12:00:00","ends_at":"2026-07-20T13:00:00"}); assert patched.status_code==200 and patched.json()['data']['exception_type_label']=='Capacitación'
    assert request('patch',f"/api/admin/availability-exceptions/{data['id']}",session,tenant_context,{"practitioner_id":str(uuid4())}).status_code==422
    disabled=request('post',f"/api/admin/availability-exceptions/{data['id']}/disable",session,tenant_context,{}); assert disabled.status_code==200 and disabled.json()['data']['status']=='inactive'
    reactivated=request('patch',f"/api/admin/availability-exceptions/{data['id']}",session,tenant_context,{"status":"active"}); assert reactivated.status_code==200

def test_create_with_location_and_room(session, tenant_context, seed):
    assert request('post','/api/admin/availability-exceptions',session,tenant_context,payload(seed, location_id=str(seed['loc'].id))).status_code==200
    assert request('post','/api/admin/availability-exceptions',session,tenant_context,payload(seed, location_id=str(seed['loc'].id), room_id=str(seed['room'].id), starts_at='2026-07-20T11:00:00', ends_at='2026-07-20T12:00:00')).status_code==200

@pytest.mark.parametrize('field', ['practitioner_id','location_id','room_id'])
def test_reject_missing_references(session, tenant_context, seed, field):
    assert request('post','/api/admin/availability-exceptions',session,tenant_context,payload(seed, **{field:str(uuid4())})).status_code==404

def test_reject_inactive_parents_and_room_mismatch(session, tenant_context, seed):
    seed['practitioner'].status='inactive'; session.commit(); assert request('post','/api/admin/availability-exceptions',session,tenant_context,payload(seed)).status_code==409
    seed['practitioner'].status='active'; seed['loc'].status='inactive'; session.commit(); assert request('post','/api/admin/availability-exceptions',session,tenant_context,payload(seed, location_id=str(seed['loc'].id))).status_code==409
    seed['loc'].status='active'; seed['room'].status='inactive'; session.commit(); assert request('post','/api/admin/availability-exceptions',session,tenant_context,payload(seed, room_id=str(seed['room'].id))).status_code==409
    seed['room'].status='active'; other=Location(organization_id=seed['org'].id, name='Otra'); session.add(other); session.commit(); assert request('post','/api/admin/availability-exceptions',session,tenant_context,payload(seed, location_id=str(other.id), room_id=str(seed['room'].id))).status_code==409
    seed['org'].status='inactive'; session.commit(); assert request('post','/api/admin/availability-exceptions',session,tenant_context,payload(seed, location_id=str(seed['loc'].id))).status_code==409

@pytest.mark.parametrize('change', [{'starts_at':'2026-07-20T11:00:00','ends_at':'2026-07-20T11:00:00'},{'exception_type':'bad'},{'extra':'x'}])
def test_reject_invalid_payload(session, tenant_context, seed, change):
    assert request('post','/api/admin/availability-exceptions',session,tenant_context,payload(seed, **change)).status_code==422

def test_overlap_allowed_exact_active_duplicate_rejected_inactive_allows_recreate(session, tenant_context, seed):
    first=request('post','/api/admin/availability-exceptions',session,tenant_context,payload(seed)); assert first.status_code==200
    assert request('post','/api/admin/availability-exceptions',session,tenant_context,payload(seed, exception_type='administrative', starts_at='2026-07-20T10:30:00', ends_at='2026-07-20T12:00:00')).status_code==200
    assert request('post','/api/admin/availability-exceptions',session,tenant_context,payload(seed)).status_code==409
    request('post',f"/api/admin/availability-exceptions/{first.json()['data']['id']}/disable",session,tenant_context,{})
    assert request('post','/api/admin/availability-exceptions',session,tenant_context,payload(seed)).status_code==200

def test_list_keeps_inactive_by_default_and_filters_by_status(session, tenant_context, seed):
    created = request('post', '/api/admin/availability-exceptions', session, tenant_context, payload(seed)); assert created.status_code == 200, created.text
    exception_id = created.json()['data']['id']
    disabled = request('post', f'/api/admin/availability-exceptions/{exception_id}/disable', session, tenant_context, {}); assert disabled.status_code == 200

    default_listing = request('get', '/api/admin/availability-exceptions', session, tenant_context).json()['data']
    assert len(default_listing) == 1 and default_listing[0]['id'] == exception_id and default_listing[0]['status'] == 'inactive'

    explicit_include_listing = request('get', '/api/admin/availability-exceptions?include_inactive=true', session, tenant_context).json()['data']
    assert len(explicit_include_listing) == 1 and explicit_include_listing[0]['id'] == exception_id and explicit_include_listing[0]['status'] == 'inactive'

    inactive_listing = request('get', '/api/admin/availability-exceptions?status=inactive', session, tenant_context).json()['data']
    assert len(inactive_listing) == 1 and inactive_listing[0]['id'] == exception_id and inactive_listing[0]['status'] == 'inactive'

    active_listing = request('get', '/api/admin/availability-exceptions?status=active', session, tenant_context).json()['data']
    assert active_listing == []

    active_only_listing = request('get', '/api/admin/availability-exceptions?include_inactive=false', session, tenant_context).json()['data']
    assert active_only_listing == []

    invalid_status = request('get', '/api/admin/availability-exceptions?status=paused', session, tenant_context)
    assert invalid_status.status_code == 400

    reactivated = request('patch', f'/api/admin/availability-exceptions/{exception_id}', session, tenant_context, {'status': 'active'}); assert reactivated.status_code == 200
    active_listing = request('get', '/api/admin/availability-exceptions?status=active', session, tenant_context).json()['data']
    assert len(active_listing) == 1 and active_listing[0]['id'] == exception_id and active_listing[0]['status'] == 'active'
