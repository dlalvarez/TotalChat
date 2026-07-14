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


def test_patch_allows_notes_but_rejects_status_changes(session, tenant_context, seed):
    r=create(session,tenant_context,seed); assert r.status_code==200, r.text
    appointment_id = r.json()['data']['id']
    patched = req('patch', f"/api/admin/appointments/{appointment_id}", session, tenant_context, {'notes': 'Nota actualizada'})
    assert patched.status_code == 200, patched.text
    assert patched.json()['data']['notes'] == 'Nota actualizada'
    rejected = req('patch', f"/api/admin/appointments/{appointment_id}", session, tenant_context, {'status': 'scheduled'})
    assert rejected.status_code == 422

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

def test_patch_reschedules_scheduled_to_free_time(session, tenant_context, seed):
    r=create(session,tenant_context,seed); assert r.status_code==200
    patched=req('patch',f"/api/admin/appointments/{r.json()['data']['id']}",session,tenant_context,{'starts_at':'2026-07-20T10:00:00','ends_at':'2026-07-20T10:30:00'})
    assert patched.status_code==200, patched.text
    assert patched.json()['data']['starts_at'].startswith('2026-07-20T10:00:00')

def test_patch_reschedule_rejects_invalid_range_block_and_practitioner_conflict(session, tenant_context, seed):
    r=create(session,tenant_context,seed); assert r.status_code==200
    aid=r.json()['data']['id']
    invalid_range=req('patch',f"/api/admin/appointments/{aid}",session,tenant_context,{'starts_at':'2026-07-20T11:00:00','ends_at':'2026-07-20T11:00:00'})
    assert invalid_range.status_code == 400
    assert invalid_range.json()['error']['code'] == 'VALIDATION_ERROR'
    assert 'starts_at must be before ends_at' in invalid_range.json()['error']['message']
    b=AvailabilityException(practitioner_id=seed['pr'].id, starts_at=datetime(2026,7,20,10,0), ends_at=datetime(2026,7,20,10,30), exception_type='meeting', status='active')
    session.add(b); session.commit()
    assert req('patch',f"/api/admin/appointments/{aid}",session,tenant_context,{'starts_at':'2026-07-20T10:00:00','ends_at':'2026-07-20T10:30:00'}).status_code==409
    b.status='inactive'; session.commit()
    other=create(session,tenant_context,seed,starts_at='2026-07-20T12:00:00',ends_at='2026-07-20T12:30:00'); assert other.status_code==200
    assert req('patch',f"/api/admin/appointments/{aid}",session,tenant_context,{'starts_at':'2026-07-20T12:15:00','ends_at':'2026-07-20T12:45:00'}).status_code==409

def test_patch_room_change_validates_room_status_location_and_conflict(session, tenant_context, seed):
    r=create(session,tenant_context,seed); assert r.status_code==200
    aid=r.json()['data']['id']
    other_room=Room(location_id=seed['loc'].id, name='Consultorio 2'); session.add(other_room); session.commit()
    patched=req('patch',f"/api/admin/appointments/{aid}",session,tenant_context,{'room_id':str(other_room.id),'starts_at':'2026-07-20T10:00:00','ends_at':'2026-07-20T10:30:00'})
    assert patched.status_code==200, patched.text
    busy=create(session,tenant_context,seed,starts_at='2026-07-20T11:00:00',ends_at='2026-07-20T11:30:00'); assert busy.status_code==200
    assert req('patch',f"/api/admin/appointments/{aid}",session,tenant_context,{'room_id':str(seed['room'].id),'starts_at':'2026-07-20T11:15:00','ends_at':'2026-07-20T11:45:00'}).status_code==409
    other_room.status='inactive'; session.commit()
    assert req('patch',f"/api/admin/appointments/{aid}",session,tenant_context,{'room_id':str(other_room.id)}).status_code==409
    other_loc=Location(organization_id=seed['org'].id, name='Otra sede'); session.add(other_loc); session.flush(); wrong_room=Room(location_id=other_loc.id, name='Externo'); session.add(wrong_room); session.commit()
    assert req('patch',f"/api/admin/appointments/{aid}",session,tenant_context,{'room_id':str(wrong_room.id)}).status_code==409

def test_patch_does_not_reschedule_inactive_status_but_allows_notes(session, tenant_context, seed):
    for endpoint in ['cancel','complete','no-show']:
        r=create(session,tenant_context,seed, starts_at='2026-07-21T09:00:00', ends_at='2026-07-21T09:30:00'); assert r.status_code==200
        aid=r.json()['data']['id']; req('post',f"/api/admin/appointments/{aid}/{endpoint}",session,tenant_context,{})
        assert req('patch',f"/api/admin/appointments/{aid}",session,tenant_context,{'starts_at':'2026-07-21T10:00:00'}).status_code==409
        ok=req('patch',f"/api/admin/appointments/{aid}",session,tenant_context,{'notes':'Solo nota'})
        assert ok.status_code==200 and ok.json()['data']['notes']=='Solo nota'

def test_create_derives_virtual_modality_from_location_and_rejects_room(session, tenant_context, seed):
    seed['loc'].is_virtual = True
    session.commit()
    with_room = create(session, tenant_context, seed)
    assert with_room.status_code == 409
    r = create(session, tenant_context, seed, room_id=None)
    assert r.status_code == 200, r.text
    data = r.json()['data']
    assert data['modality'] == 'virtual'
    assert data['room_id'] is None
    assert data['virtual_link_status'] == 'pending'


def test_rejects_external_modality_and_presential_virtual_link_data(session, tenant_context, seed):
    assert create(session, tenant_context, seed, modality='virtual').status_code == 422
    r = create(session, tenant_context, seed, virtual_meeting_url='https://meet.example/manual')
    assert r.status_code == 409


def test_virtual_link_manual_fields_sent_and_cancelled(session, tenant_context, seed):
    seed['loc'].is_virtual = True
    session.commit()
    r = create(session, tenant_context, seed, room_id=None, virtual_meeting_url='https://meet.example/manual')
    assert r.status_code == 200, r.text
    data = r.json()['data']
    assert data['modality'] == 'virtual'
    assert data['virtual_link_status'] == 'created'
    assert data['virtual_link_provider'] == 'manual'
    sent = req('patch', f"/api/admin/appointments/{data['id']}", session, tenant_context, {'virtual_link_status': 'sent'})
    assert sent.status_code == 200, sent.text
    assert sent.json()['data']['virtual_link_status'] == 'sent'
    assert sent.json()['data']['virtual_link_sent_at'] is not None
    cancelled = req('post', f"/api/admin/appointments/{data['id']}/cancel", session, tenant_context, {})
    assert cancelled.status_code == 200
    assert cancelled.json()['data']['virtual_link_status'] == 'cancelled'


def test_virtual_link_requires_url_for_created_and_sent(session, tenant_context, seed):
    seed['loc'].is_virtual = True
    session.commit()
    by_id = create(session, tenant_context, seed, room_id=None, virtual_meeting_id='123')
    assert by_id.status_code == 200, by_id.text
    data = by_id.json()['data']
    assert data['virtual_link_status'] == 'pending'
    assert data['virtual_link_created_mode'] is None
    assert data['virtual_link_provider'] is None
    sent_without_url = req('patch', f"/api/admin/appointments/{data['id']}", session, tenant_context, {'virtual_link_status': 'sent'})
    assert sent_without_url.status_code == 409
    created_without_url = req('patch', f"/api/admin/appointments/{data['id']}", session, tenant_context, {'virtual_link_status': 'created'})
    assert created_without_url.status_code == 409


def test_clearing_virtual_url_resets_link_state(session, tenant_context, seed):
    seed['loc'].is_virtual = True
    session.commit()
    r = create(session, tenant_context, seed, room_id=None, starts_at='2026-07-20T13:00:00', ends_at='2026-07-20T13:30:00', virtual_meeting_url='https://meet.example/manual')
    assert r.status_code == 200, r.text
    data = r.json()['data']
    sent = req('patch', f"/api/admin/appointments/{data['id']}", session, tenant_context, {'virtual_link_status': 'sent'})
    assert sent.status_code == 200, sent.text
    cleared = req('patch', f"/api/admin/appointments/{data['id']}", session, tenant_context, {'virtual_meeting_url': None, 'virtual_meeting_id': None, 'virtual_access_code': None})
    assert cleared.status_code == 200, cleared.text
    out = cleared.json()['data']
    assert out['virtual_link_status'] == 'pending'
    assert out['virtual_link_sent_at'] is None
    assert out['virtual_link_created_mode'] is None
    assert out['virtual_link_provider'] is None
