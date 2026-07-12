from datetime import datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.admin.dependencies import get_admin_tenant_context, get_db_session
from app.main import app
from app.models.tenant import AvailabilityException, Booking, Location, Organization, OrganizationPractitioner, Patient, Practitioner, PractitionerService, Room
from app.tenancy.context import TenantContext

TABLES = [Organization.__table__, Location.__table__, Room.__table__, Practitioner.__table__, OrganizationPractitioner.__table__, PractitionerService.__table__, Patient.__table__, AvailabilityException.__table__, Booking.__table__]
@pytest.fixture()
def tenant_context(): return TenantContext(tenant_id=uuid4(), slug='clinica', schema_name='tenant_clinica')
@pytest.fixture()
def session():
    engine=create_engine('sqlite:///:memory:', connect_args={'check_same_thread':False}, poolclass=StaticPool)
    for t in TABLES: t.create(engine)
    with Session(engine) as s: yield s
@pytest.fixture()
def seed(session):
    org=Organization(name='Clínica Vida', organization_type='clinic'); loc=Location(organization_id=org.id, name='Sede Norte'); room=Room(location_id=loc.id, name='Consultorio 1'); pr=Practitioner(full_name='Dra. Ana'); patient=Patient(full_name='María Gómez')
    session.add_all([org, pr, patient]); session.flush(); loc.organization_id=org.id; session.add(loc); session.flush(); room.location_id=loc.id; session.add(room); session.flush(); rel=OrganizationPractitioner(organization_id=org.id, practitioner_id=pr.id); svc=PractitionerService(organization_id=org.id, practitioner_id=pr.id, name='Consulta general', duration_minutes=30)
    session.add_all([rel, svc]); session.commit(); return {'org':org,'loc':loc,'room':room,'pr':pr,'rel':rel,'svc':svc,'patient':patient}
def install(s, tc):
    def os(): yield s
    app.dependency_overrides[get_db_session]=os; app.dependency_overrides[get_admin_tenant_context]=lambda: tc
def req(method,path,s,tc,json=None):
    install(s,tc)
    try: return getattr(TestClient(app),method)(path, json=json, headers={'X-TotalChat-Tenant-Id':str(tc.tenant_id)}) if json is not None else getattr(TestClient(app),method)(path, headers={'X-TotalChat-Tenant-Id':str(tc.tenant_id)})
    finally: app.dependency_overrides.clear()
def payload(seed, **kw):
    data={'organization_id':str(seed['org'].id),'location_id':str(seed['loc'].id),'room_id':str(seed['room'].id),'practitioner_id':str(seed['pr'].id),'practitioner_service_id':str(seed['svc'].id),'patient_id':str(seed['patient'].id),'starts_at':'2026-07-20T09:00:00','ends_at':'2026-07-20T09:30:00','notes':'Traer resultados'}; data.update(kw); return data
def create(s,tc,seed,**kw): return req('post','/api/admin/appointments',s,tc,payload(seed,**kw))

def test_create_list_detail_status_actions_and_no_schema(session, tenant_context, seed):
    r=create(session,tenant_context,seed); assert r.status_code==200, r.text
    data=r.json()['data']; assert data['status']=='scheduled' and data['status_label']=='Programada' and data['patient_name']=='María Gómez' and 'schema_name' not in data
    assert req('get','/api/admin/appointments?date=2026-07-20',session,tenant_context).json()['data'][0]['id']==data['id']
    assert req('get',f"/api/admin/appointments/{data['id']}",session,tenant_context).status_code==200
    assert req('post',f"/api/admin/appointments/{data['id']}/cancel",session,tenant_context,{}).json()['data']['status']=='cancelled'
    second=create(session,tenant_context,seed); assert second.status_code==200
    sid=second.json()['data']['id']; assert req('post',f"/api/admin/appointments/{sid}/complete",session,tenant_context,{}).json()['data']['status']=='completed'
    third=create(session,tenant_context,seed); assert third.status_code==200
    assert req('post',f"/api/admin/appointments/{third.json()['data']['id']}/no-show",session,tenant_context,{}).json()['data']['status']=='no_show'

def test_reject_invalid_range_and_inactive_parents(session, tenant_context, seed):
    assert create(session,tenant_context,seed, starts_at='2026-07-20T09:00:00', ends_at='2026-07-20T09:00:00').status_code==422
    for obj in ['org','loc','room','pr']:
        seed[obj].status='inactive'; session.commit(); assert create(session,tenant_context,seed).status_code==409; seed[obj].status='active'; session.commit()
    seed['rel'].status='inactive'; session.commit(); assert create(session,tenant_context,seed).status_code==409; seed['rel'].status='active'; session.commit()
    other=Practitioner(full_name='Dr. Otro'); session.add(other); session.flush(); seed['svc'].practitioner_id=other.id; session.commit(); assert create(session,tenant_context,seed).status_code==409
    seed['svc'].practitioner_id=seed['pr'].id; other_org=Organization(name='Otra', organization_type='clinic'); session.add(other_org); session.flush(); seed['svc'].organization_id=other_org.id; session.commit(); assert create(session,tenant_context,seed).status_code==409

def test_conflicts_with_active_blocks_by_scope_and_allows_inactive(session, tenant_context, seed):
    b=AvailabilityException(practitioner_id=seed['pr'].id, starts_at=datetime(2026,7,20,8,30), ends_at=datetime(2026,7,20,9,15), exception_type='meeting', status='active')
    session.add(b); session.commit(); assert create(session,tenant_context,seed).status_code==409
    b.status='inactive'; session.commit(); assert create(session,tenant_context,seed).status_code==200
    req('post',f"/api/admin/appointments/{req('get','/api/admin/appointments',session,tenant_context).json()['data'][0]['id']}/cancel",session,tenant_context,{})
    b.status='active'; b.location_id=seed['loc'].id; session.commit(); assert create(session,tenant_context,seed).status_code==409
    b.location_id=None; b.room_id=seed['room'].id; session.commit(); assert create(session,tenant_context,seed).status_code==409

def test_conflicts_with_scheduled_practitioner_and_room_only(session, tenant_context, seed):
    assert create(session,tenant_context,seed).status_code==200
    r=create(session,tenant_context,seed, starts_at='2026-07-20T09:15:00', ends_at='2026-07-20T09:45:00'); assert r.status_code==409 and r.json()['error']['code']=='CONFLICT'
    assert create(session,tenant_context,seed, starts_at='2026-07-20T09:30:00', ends_at='2026-07-20T10:00:00').status_code==200

def test_cancelled_completed_no_show_do_not_block(session, tenant_context, seed):
    for endpoint in ['cancel','complete','no-show']:
        r=create(session,tenant_context,seed); assert r.status_code==200
        req('post',f"/api/admin/appointments/{r.json()['data']['id']}/{endpoint}",session,tenant_context,{})
        assert create(session,tenant_context,seed).status_code==200
        latest=req('get','/api/admin/appointments?status=scheduled',session,tenant_context).json()['data'][-1]
        req('post',f"/api/admin/appointments/{latest['id']}/cancel",session,tenant_context,{})

def test_requires_tenant_auth(session):
    app.dependency_overrides[get_db_session]=lambda: iter([session])
    try:
        r=TestClient(app).get('/api/admin/appointments')
    finally: app.dependency_overrides.clear()
    assert r.status_code==401
