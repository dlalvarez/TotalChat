from datetime import date, time
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.admin.dependencies import get_admin_tenant_context, get_db_session
from app.main import app
from app.models.tenant import AvailabilityRule, Organization, OrganizationPractitioner, Practitioner, PractitionerService
from app.tenancy.context import TenantContext

TENANT_TABLES = [Organization.__table__, Practitioner.__table__, OrganizationPractitioner.__table__, PractitionerService.__table__, AvailabilityRule.__table__]

@pytest.fixture()
def tenant_context(): return TenantContext(tenant_id=uuid4(), slug="clinica", schema_name="tenant_clinica")
@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    for table in TENANT_TABLES: table.create(engine)
    with Session(engine) as s: yield s
@pytest.fixture()
def seed(session):
    org=Organization(name="Clínica Vida", organization_type="clinic"); practitioner=Practitioner(full_name="Dra. Ana")
    session.add_all([org, practitioner]); session.flush()
    rel=OrganizationPractitioner(organization_id=org.id, practitioner_id=practitioner.id, role="member")
    svc=PractitionerService(organization_id=org.id, practitioner_id=practitioner.id, name="Consulta", duration_minutes=30)
    session.add_all([rel, svc]); session.commit(); return {"org":org,"practitioner":practitioner,"rel":rel,"service":svc}

def install(s, tc):
    def override_session():
        yield s
    app.dependency_overrides[get_db_session] = override_session
    app.dependency_overrides[get_admin_tenant_context] = lambda: tc

def clear(): app.dependency_overrides.clear()
def client_post(path, payload, s, tc):
    install(s, tc)
    try: return TestClient(app).post(path, json=payload, headers={"X-TotalChat-Tenant-Id": str(tc.tenant_id)})
    finally: clear()
def client_get(path, s, tc):
    install(s, tc)
    try: return TestClient(app).get(path, headers={"X-TotalChat-Tenant-Id": str(tc.tenant_id)})
    finally: clear()
def client_patch(path, payload, s, tc):
    install(s, tc)
    try: return TestClient(app).patch(path, json=payload, headers={"X-TotalChat-Tenant-Id": str(tc.tenant_id)})
    finally: clear()

def payload(seed, **kw):
    data={"organization_id":str(seed["org"].id),"practitioner_id":str(seed["practitioner"].id),"practitioner_service_id":None,"day_of_week":0,"start_time":"08:00:00","end_time":"12:00:00","valid_from":"2026-07-01","valid_to":None}
    data.update(kw); return data

def test_create_general_and_service_rule_list_detail_no_schema(session, tenant_context, seed):
    r1=client_post('/api/admin/practitioner-availability-rules', payload(seed), session, tenant_context)
    assert r1.status_code == 200, r1.text
    r2=client_post('/api/admin/practitioner-availability-rules', payload(seed, practitioner_service_id=str(seed['service'].id)), session, tenant_context)
    assert r2.status_code == 200, r2.text
    data=r1.json()['data']; assert data['scope_label']=='Todos los servicios'; assert data['organization_name']=='Clínica Vida'; assert 'schema_name' not in data
    listing=client_get('/api/admin/practitioner-availability-rules', session, tenant_context).json()['data']; assert len(listing)==2
    detail=client_get(f"/api/admin/practitioner-availability-rules/{data['id']}", session, tenant_context); assert detail.status_code==200

@pytest.mark.parametrize('field', ['organization_id','practitioner_id','practitioner_service_id'])
def test_reject_missing_references(session, tenant_context, seed, field):
    response=client_post('/api/admin/practitioner-availability-rules', payload(seed, **{field:str(uuid4())}), session, tenant_context)
    assert response.status_code == 404

@pytest.mark.parametrize('change,msg', [({'start_time':'12:00:00','end_time':'12:00:00'},422),({'valid_to':'2026-06-30'},422),({'day_of_week':7},422)])
def test_reject_invalid_payload(session, tenant_context, seed, change, msg):
    assert client_post('/api/admin/practitioner-availability-rules', payload(seed, **change), session, tenant_context).status_code == msg

def test_reject_inactive_parents_and_relation_and_service_mismatch(session, tenant_context, seed):
    seed['org'].status='inactive'; session.commit(); assert client_post('/api/admin/practitioner-availability-rules', payload(seed), session, tenant_context).status_code==409
    seed['org'].status='active'; seed['practitioner'].status='inactive'; session.commit(); assert client_post('/api/admin/practitioner-availability-rules', payload(seed), session, tenant_context).status_code==409
    seed['practitioner'].status='active'; seed['rel'].status='inactive'; session.commit(); assert client_post('/api/admin/practitioner-availability-rules', payload(seed), session, tenant_context).status_code==409
    seed['rel'].status='active'; seed['service'].status='inactive'; session.commit(); assert client_post('/api/admin/practitioner-availability-rules', payload(seed, practitioner_service_id=str(seed['service'].id)), session, tenant_context).status_code==409
    other=Practitioner(full_name='Dr. Otro'); session.add(other); session.flush(); bad=PractitionerService(organization_id=seed['org'].id, practitioner_id=other.id, name='Bad', duration_minutes=30); session.add(bad); session.commit(); assert client_post('/api/admin/practitioner-availability-rules', payload(seed, practitioner_service_id=str(bad.id)), session, tenant_context).status_code==409

def test_overlap_non_overlap_historical_patch_disable_reactivate(session, tenant_context, seed):
    first=client_post('/api/admin/practitioner-availability-rules', payload(seed, start_time='08:00:00', end_time='10:00:00', valid_to='2026-07-31'), session, tenant_context); assert first.status_code==200
    assert client_post('/api/admin/practitioner-availability-rules', payload(seed, start_time='09:00:00', end_time='11:00:00', valid_to='2026-08-31'), session, tenant_context).status_code==409
    assert client_post('/api/admin/practitioner-availability-rules', payload(seed, start_time='10:00:00', end_time='12:00:00', valid_to='2026-07-31'), session, tenant_context).status_code==200
    rid=first.json()['data']['id']
    patched=client_patch(f'/api/admin/practitioner-availability-rules/{rid}', {'day_of_week':1,'start_time':'07:00:00','end_time':'09:00:00','valid_from':'2026-07-01','valid_to':'2026-07-31'}, session, tenant_context); assert patched.status_code==200
    assert client_patch(f'/api/admin/practitioner-availability-rules/{rid}', {'organization_id':str(uuid4())}, session, tenant_context).status_code==422
    disabled=client_post(f'/api/admin/practitioner-availability-rules/{rid}/disable', {}, session, tenant_context); assert disabled.status_code==200 and disabled.json()['data']['status']=='inactive'
    # inactive historical overlap allowed
    assert client_post('/api/admin/practitioner-availability-rules', payload(seed, day_of_week=1, start_time='07:30:00', end_time='08:30:00'), session, tenant_context).status_code==200
    seed['rel'].status='inactive'; session.commit(); assert client_patch(f'/api/admin/practitioner-availability-rules/{rid}', {'status':'active'}, session, tenant_context).status_code==409
