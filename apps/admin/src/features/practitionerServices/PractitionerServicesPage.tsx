import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { PageHeader } from '../../components/layout/PageHeader';
import { Button } from '../../components/ui/Button';
import { SectionCard } from '../../components/ui/Card';
import { DataTableShell } from '../../components/ui/DataTable';
import { FieldWrapper, Input, Select } from '../../components/ui/Form';
import { EmptyState, ErrorState, LoadingState } from '../../components/ui/States';
import { adminResourcesApi, type PractitionerService } from '../../api/adminResources';
import type { AdminTenant } from '../../config/tenant';
import { NameEditButton, StatusAction, StatusBadge } from '../adminResourceUtils';

const schema = z.object({ organization_id: z.string().min(1, 'Selecciona una organización'), practitioner_id: z.string().min(1, 'Selecciona un profesional'), name: z.string().trim().min(1, 'Nombre requerido'), description: z.string().optional(), duration_minutes: z.coerce.number().int().positive('La duración debe ser positiva'), requires_payment: z.boolean().default(true) });
type FormValues = z.infer<typeof schema>;
const defaults = (s?: PractitionerService): FormValues => ({ organization_id: s?.organization_id ?? '', practitioner_id: s?.practitioner_id ?? '', name: s?.name ?? '', description: s?.description ?? '', duration_minutes: s?.duration_minutes ?? 30, requires_payment: s?.requires_payment ?? true });

export function PractitionerServicesPage({ tenant }: { tenant: AdminTenant }) {
  const [showForm, setShowForm] = useState(false); const [editing, setEditing] = useState<PractitionerService | null>(null); const [feedback, setFeedback] = useState<string | null>(null);
  const qc = useQueryClient(); const servicesKey = useMemo(() => ['practitioner-services', tenant.id], [tenant.id]);
  const services = useQuery({ queryKey: servicesKey, queryFn: () => adminResourcesApi.listPractitionerServices(tenant.id) });
  const organizations = useQuery({ queryKey: ['organizations', tenant.id], queryFn: () => adminResourcesApi.listOrganizations(tenant.id) });
  const relations = useQuery({ queryKey: ['organization-practitioners', tenant.id], queryFn: () => adminResourcesApi.listOrganizationPractitioners(tenant.id) });
  const form = useForm<FormValues>({ resolver: zodResolver(schema), defaultValues: defaults() });
  const selectedOrganizationId = form.watch('organization_id');
  const activeOrganizations = (organizations.data ?? []).filter((o) => o.status === 'active');
  const activeRelations = (relations.data ?? []).filter((r) => r.status === 'active' && r.organization_status === 'active' && r.practitioner_status === 'active');
  const practitionersForOrganization = activeRelations.filter((r) => r.organization_id === selectedOrganizationId);
  const closeForm = () => { setEditing(null); setShowForm(false); form.reset(defaults()); };
  const save = useMutation({ mutationFn: (v: FormValues) => editing ? adminResourcesApi.updatePractitionerService(tenant.id, editing.id, { name: v.name, description: v.description || null, duration_minutes: v.duration_minutes, requires_payment: v.requires_payment }) : adminResourcesApi.createPractitionerService(tenant.id, { ...v, description: v.description || null }), onSuccess: async () => { setFeedback(editing ? 'Servicio actualizado correctamente.' : 'Servicio creado correctamente.'); closeForm(); await qc.invalidateQueries({ queryKey: servicesKey }); } });
  const statusAction = useMutation({ mutationFn: (s: PractitionerService) => s.status === 'active' ? adminResourcesApi.disablePractitionerService(tenant.id, s.id) : adminResourcesApi.activatePractitionerService(tenant.id, s.id), onSuccess: async (_updated, s) => { setFeedback(s.status === 'active' ? 'Servicio inactivado correctamente.' : 'Servicio activado correctamente.'); await qc.invalidateQueries({ queryKey: servicesKey }); } });
  const startEdit = (s: PractitionerService) => { setEditing(s); form.reset(defaults(s)); setShowForm(true); };

  return <><PageHeader eyebrow="Fase 6B.6 · servicios del profesional" title="Servicios" description="Administra servicios por profesional y organización. Sin precios, modalidades ni disponibilidad en esta fase." actions={<Button onClick={() => showForm ? closeForm() : setShowForm(true)}>{showForm ? 'Cerrar formulario' : 'Crear servicio'}</Button>} />
  {feedback ? <div className="mb-4 rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-sm font-medium text-emerald-800">{feedback}</div> : null}{save.isError ? <div className="mb-4"><ErrorState description={(save.error as Error).message} /></div> : null}{statusAction.isError ? <div className="mb-4"><ErrorState description={(statusAction.error as Error).message} /></div> : null}
  {showForm ? <SectionCard title={editing ? `Editar ${editing.name}` : 'Nuevo servicio'} description={editing ? `${editing.organization_name ?? 'Organización'} · ${editing.practitioner_name ?? 'Profesional'}. Organización y profesional no se cambian; inactiva y crea otro servicio si hubo error.` : 'Selecciona organización activa y profesional asociado activo por nombre.'}><form className="grid gap-4 md:grid-cols-2" onSubmit={form.handleSubmit((v) => save.mutate(v))}>
    <FieldWrapper label="Organización *" error={form.formState.errors.organization_id?.message}><Select {...form.register('organization_id')} disabled={Boolean(editing)}><option value="">Selecciona una organización</option>{(editing ? organizations.data ?? [] : activeOrganizations).map((o) => <option key={o.id} value={o.id}>{o.name}</option>)}</Select></FieldWrapper>
    <FieldWrapper label="Profesional *" error={form.formState.errors.practitioner_id?.message} hint={!editing && selectedOrganizationId && practitionersForOrganization.length === 0 ? 'No hay profesionales activos asociados a esta organización. Asocia primero un profesional en Profesionales por organización.' : 'Solo profesionales con relación activa.'}><Select {...form.register('practitioner_id')} disabled={Boolean(editing) || !selectedOrganizationId}><option value="">Selecciona un profesional</option>{(editing ? [{ practitioner_id: editing.practitioner_id, practitioner_name: editing.practitioner_name }] : practitionersForOrganization).map((r) => <option key={r.practitioner_id} value={r.practitioner_id}>{r.practitioner_name}</option>)}</Select></FieldWrapper>
    <FieldWrapper label="Nombre del servicio *" error={form.formState.errors.name?.message}><Input {...form.register('name')} placeholder="Consulta pediátrica" /></FieldWrapper>
    <FieldWrapper label="Duración en minutos *" error={form.formState.errors.duration_minutes?.message}><Input type="number" min={1} {...form.register('duration_minutes')} /></FieldWrapper>
    <FieldWrapper label="Descripción"><Input {...form.register('description')} placeholder="Detalle opcional" /></FieldWrapper>
    <label className="flex items-center gap-2 pt-8 text-sm font-semibold text-slate-700"><input type="checkbox" {...form.register('requires_payment')} /> ¿Requiere pago?</label>
    <div className="flex gap-2 md:col-span-2"><Button type="submit" disabled={save.isPending}>{save.isPending ? 'Guardando…' : 'Guardar servicio'}</Button>{editing ? <Button type="button" variant="secondary" onClick={closeForm}>Cancelar</Button> : null}</div>
  </form></SectionCard> : null}
  <div className="mt-6"><SectionCard title="Servicios configurados" description="El nombre abre edición; la acción derecha activa o inactiva sin borrado físico.">{services.isLoading ? <LoadingState label="Cargando servicios…" /> : null}{services.isError ? <ErrorState description={(services.error as Error).message} /> : null}{services.isSuccess && services.data.length === 0 ? <EmptyState title="Aún no hay servicios configurados." description="Crea el primer servicio para un profesional asociado a una organización." /> : null}{services.isSuccess && services.data.length > 0 ? <DataTableShell columns={['Servicio', 'Profesional', 'Organización', 'Duración', 'Requiere pago', 'Estado', 'Acciones']} rows={services.data.map((s) => [<NameEditButton name={s.name} onEdit={() => startEdit(s)} />, <span>{s.practitioner_name}{s.practitioner_status === 'inactive' ? ' (inactivo)' : ''}</span>, <span>{s.organization_name}{s.organization_status === 'inactive' ? ' (inactiva)' : ''}{s.organization_practitioner_status === 'inactive' ? ' · relación inactiva' : ''}</span>, `${s.duration_minutes} min`, s.requires_payment ? 'Sí' : 'No', <StatusBadge status={s.status} />, <StatusAction status={s.status} entityName={s.name} disabled={statusAction.isPending} onInactivate={() => statusAction.mutate(s)} onActivate={() => statusAction.mutate(s)} />])} /> : null}</SectionCard></div></>;
}
