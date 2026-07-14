import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { PageHeader } from '../../components/layout/PageHeader';
import { SectionCard } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { FieldWrapper, Input, Select } from '../../components/ui/Form';
import { EmptyState, ErrorState, LoadingState } from '../../components/ui/States';
import { adminResourcesApi, type CreatePatientPayload, type Patient, type PatientProfileStatus, type UpdatePatientPayload } from '../../api/adminResources';
import type { AdminTenant } from '../../config/tenant';
import { PatientForm } from './PatientForm';
import { PatientList } from './PatientList';
import { PATIENT_PROFILE_OPTIONS } from './patientUtils';

export function PatientsPage({ tenant }: { tenant: AdminTenant }) {
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<Patient | null>(null);
  const [q, setQ] = useState('');
  const [profileStatus, setProfileStatus] = useState<PatientProfileStatus | ''>('');
  const [feedback, setFeedback] = useState<string | null>(null);
  const qc = useQueryClient();
  const filters = useMemo(() => ({ q: q.trim() || undefined, profile_status: profileStatus || undefined }), [q, profileStatus]);
  const key = useMemo(() => ['patients', tenant.id, filters], [tenant.id, filters]);
  const patients = useQuery({ queryKey: key, queryFn: () => adminResourcesApi.listPatients(tenant.id, filters) });
  const allPatients = useQuery({ queryKey: ['patients-summary', tenant.id], queryFn: () => adminResourcesApi.listPatients(tenant.id) });
  const invalidate = async () => { await Promise.all([qc.invalidateQueries({ queryKey: ['patients', tenant.id] }), qc.invalidateQueries({ queryKey: ['patients-summary', tenant.id] })]); };
  const closeForm = () => { setShowForm(false); setEditing(null); };
  const save = useMutation({ mutationFn: (payload: CreatePatientPayload | UpdatePatientPayload) => editing ? adminResourcesApi.updatePatient(tenant.id, editing.id, payload as UpdatePatientPayload) : adminResourcesApi.createPatient(tenant.id, payload as CreatePatientPayload), onSuccess: async () => { setFeedback(editing ? 'Paciente actualizado correctamente.' : 'Paciente creado correctamente.'); closeForm(); await invalidate(); } });
  const statusAction = useMutation({ mutationFn: ({ patient, action }: { patient: Patient; action: 'disable' | 'reactivate' }) => action === 'disable' ? adminResourcesApi.disablePatient(tenant.id, patient.id) : adminResourcesApi.reactivatePatient(tenant.id, patient.id), onSuccess: async (_updated, variables) => { setFeedback(variables.action === 'disable' ? 'Paciente inactivado correctamente.' : 'Paciente reactivado correctamente.'); await invalidate(); } });
  const summary = allPatients.data ?? [];
  const inactive = summary.filter((patient) => patient.profile_status === 'inactive').length;
  const active = summary.length - inactive;
  const startEdit = (patient: Patient) => { setEditing(patient); setShowForm(true); };

  return <>
    <PageHeader eyebrow="Fase 6B.12 · pacientes" title="Pacientes" description="Gestiona pacientes administrativos básicos del tenant. No se capturan datos clínicos ni se eliminan registros físicamente." actions={<Button onClick={() => { if (showForm) closeForm(); else setShowForm(true); }}>{showForm ? 'Cerrar formulario' : 'Crear paciente'}</Button>} />
    {feedback ? <div className="mb-4 rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-sm font-medium text-emerald-800">{feedback}</div> : null}
    {save.isError ? <div className="mb-4"><ErrorState description={(save.error as Error).message} /></div> : null}
    {statusAction.isError ? <div className="mb-4"><ErrorState description={(statusAction.error as Error).message} /></div> : null}
    <div className="mb-6 grid gap-4 md:grid-cols-3">
      <SectionCard title="Total pacientes"><p className="text-3xl font-bold text-slate-950">{summary.length}</p></SectionCard>
      <SectionCard title="Activos / trazables"><p className="text-3xl font-bold text-emerald-700">{active}</p></SectionCard>
      <SectionCard title="Inactivos visibles"><p className="text-3xl font-bold text-slate-700">{inactive}</p></SectionCard>
    </div>
    {showForm ? <SectionCard title={editing ? `Editar ${editing.full_name}` : 'Nuevo paciente'} description="Datos administrativos básicos. El estado inicial desde consola es Mínimo."><PatientForm patient={editing} pending={save.isPending} onCancel={closeForm} onSubmit={(payload) => save.mutate(payload)} /></SectionCard> : null}
    <SectionCard title="Filtros" description="Búsqueda por nombre, documento, teléfono o email."><div className="grid gap-4 md:grid-cols-2"><FieldWrapper label="Buscar"><Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Nombre, documento, teléfono o email" /></FieldWrapper><FieldWrapper label="Estado"><Select value={profileStatus} onChange={(e) => setProfileStatus(e.target.value as PatientProfileStatus | '')}><option value="">Todos</option>{PATIENT_PROFILE_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}</Select></FieldWrapper></div></SectionCard>
    <SectionCard title="Listado de pacientes" description={`Tenant activo: ${tenant.label}. Los pacientes inactivos permanecen visibles por trazabilidad.`}>{patients.isLoading ? <LoadingState label="Cargando pacientes…" /> : null}{patients.isError ? <ErrorState description={(patients.error as Error).message} /> : null}{patients.isSuccess && patients.data.length === 0 ? <EmptyState title="Sin pacientes" description="Crea pacientes administrativos antes de registrar citas manuales." /> : null}{patients.isSuccess && patients.data.length > 0 ? <PatientList patients={patients.data} actionPending={statusAction.isPending} onEdit={startEdit} onDisable={(patient) => statusAction.mutate({ patient, action: 'disable' })} onReactivate={(patient) => statusAction.mutate({ patient, action: 'reactivate' })} /> : null}</SectionCard>
  </>;
}
