import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { PageHeader } from '../../components/layout/PageHeader';
import { Button } from '../../components/ui/Button';
import { SectionCard } from '../../components/ui/Card';
import { DataTableShell } from '../../components/ui/DataTable';
import { FieldWrapper, Select } from '../../components/ui/Form';
import { EmptyState, ErrorState, LoadingState } from '../../components/ui/States';
import { adminResourcesApi, ORGANIZATION_PRACTITIONER_ROLE_OPTIONS, organizationPractitionerRoleLabel, type OrganizationPractitioner } from '../../api/adminResources';
import type { AdminTenant } from '../../config/tenant';
import { NameEditButton, StatusAction, StatusBadge } from '../adminResourceUtils';

const schema = z.object({ organization_id: z.string().min(1, 'Selecciona una organización'), practitioner_id: z.string().min(1, 'Selecciona un profesional'), role: z.string().default('member') });
type FormValues = z.infer<typeof schema>;
const defaults = (relation?: OrganizationPractitioner): FormValues => ({ organization_id: relation?.organization_id ?? '', practitioner_id: relation?.practitioner_id ?? '', role: relation?.role ?? 'member' });

export function OrganizationPractitionersPage({ tenant }: { tenant: AdminTenant }) {
  const [showForm, setShowForm] = useState(false); const [editing, setEditing] = useState<OrganizationPractitioner | null>(null); const [feedback, setFeedback] = useState<string | null>(null);
  const qc = useQueryClient(); const relationsKey = useMemo(() => ['organization-practitioners', tenant.id], [tenant.id]);
  const organizationsKey = useMemo(() => ['organizations', tenant.id], [tenant.id]); const practitionersKey = useMemo(() => ['practitioners', tenant.id], [tenant.id]);
  const relations = useQuery({ queryKey: relationsKey, queryFn: () => adminResourcesApi.listOrganizationPractitioners(tenant.id) });
  const organizations = useQuery({ queryKey: organizationsKey, queryFn: () => adminResourcesApi.listOrganizations(tenant.id) });
  const practitioners = useQuery({ queryKey: practitionersKey, queryFn: () => adminResourcesApi.listPractitioners(tenant.id) });
  const form = useForm<FormValues>({ resolver: zodResolver(schema), defaultValues: defaults() });
  const activeOrganizations = (organizations.data ?? []).filter((o) => o.status === 'active'); const activePractitioners = (practitioners.data ?? []).filter((p) => p.status === 'active');
  const closeForm = () => { setEditing(null); setShowForm(false); form.reset(defaults()); };
  const save = useMutation({ mutationFn: (v: FormValues) => editing ? adminResourcesApi.updateOrganizationPractitioner(tenant.id, editing.organization_id, editing.practitioner_id, { role: v.role }) : adminResourcesApi.createOrganizationPractitioner(tenant.id, { organization_id: v.organization_id, practitioner_id: v.practitioner_id, role: v.role }), onSuccess: async () => { setFeedback(editing ? 'Rol actualizado correctamente.' : 'Profesional asociado correctamente.'); closeForm(); await qc.invalidateQueries({ queryKey: relationsKey }); } });
  const statusAction = useMutation({ mutationFn: (r: OrganizationPractitioner) => r.status === 'active' ? adminResourcesApi.disableOrganizationPractitioner(tenant.id, r.organization_id, r.practitioner_id) : adminResourcesApi.activateOrganizationPractitioner(tenant.id, r.organization_id, r.practitioner_id), onSuccess: async (_updated, r) => { setFeedback(r.status === 'active' ? 'Relación inactivada correctamente.' : 'Relación activada correctamente.'); await qc.invalidateQueries({ queryKey: relationsKey }); } });
  const startEdit = (r: OrganizationPractitioner) => { setEditing(r); form.reset(defaults(r)); setShowForm(true); };

  return <><PageHeader eyebrow="Fase 6B.5 · relación organización-profesional" title="Profesionales por organización" description="Asocia profesionales activos a organizaciones activas sin mostrar UUIDs ni borrar relaciones." actions={<Button onClick={() => showForm ? closeForm() : setShowForm(true)}>{showForm ? 'Cerrar formulario' : 'Asociar profesional'}</Button>} />
  {feedback ? <div className="mb-4 rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-sm font-medium text-emerald-800">{feedback}</div> : null}{save.isError ? <div className="mb-4"><ErrorState description={(save.error as Error).message} /></div> : null}{statusAction.isError ? <div className="mb-4"><ErrorState description={(statusAction.error as Error).message} /></div> : null}
  {showForm ? <SectionCard title={editing ? `Editar rol de ${editing.practitioner_name ?? 'profesional'}` : 'Nueva asociación'} description={editing ? 'La pareja organización-profesional no se cambia; si fue un error, inactiva y crea otra relación.' : 'Selecciona por nombre. Solo se ofrecen organizaciones y profesionales activos.'}><form className="grid gap-4 md:grid-cols-3" onSubmit={form.handleSubmit((v) => save.mutate(v))}>
    <FieldWrapper label="Organización" hint="Selector por nombre; UUID interno." error={form.formState.errors.organization_id?.message}><Select {...form.register('organization_id')} disabled={Boolean(editing) || organizations.isLoading}><option value="">Selecciona una organización</option>{(editing ? organizations.data ?? [] : activeOrganizations).map((o) => <option key={o.id} value={o.id}>{o.name}</option>)}</Select></FieldWrapper>
    <FieldWrapper label="Profesional" hint="Selector por nombre; UUID interno." error={form.formState.errors.practitioner_id?.message}><Select {...form.register('practitioner_id')} disabled={Boolean(editing) || practitioners.isLoading}><option value="">Selecciona un profesional</option>{(editing ? practitioners.data ?? [] : activePractitioners).map((p) => <option key={p.id} value={p.id}>{p.full_name}</option>)}</Select></FieldWrapper>
    <FieldWrapper label="Rol" error={form.formState.errors.role?.message}><Select {...form.register('role')}>{ORGANIZATION_PRACTITIONER_ROLE_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}</Select></FieldWrapper>
    <div className="flex gap-2 md:col-span-3"><Button type="submit" disabled={save.isPending || (!editing && (activeOrganizations.length === 0 || activePractitioners.length === 0))}>{save.isPending ? 'Guardando…' : 'Guardar cambios'}</Button>{editing ? <Button type="button" variant="secondary" onClick={closeForm}>Cancelar</Button> : null}</div>
  </form></SectionCard> : null}
  <div className="mt-6"><SectionCard title="Relaciones organización-profesional" description={`Tenant activo: ${tenant.label}. Las relaciones inactivas se conservan.`}>{relations.isLoading ? <LoadingState label="Cargando relaciones…" /> : null}{relations.isError ? <ErrorState description={(relations.error as Error).message} /> : null}{relations.isSuccess && relations.data.length === 0 ? <EmptyState title="Sin relaciones" description="Asocia el primer profesional a una organización activa." /> : null}{relations.isSuccess && relations.data.length > 0 ? <DataTableShell columns={['Organización', 'Profesional', 'Rol', 'Estado', 'Acciones']} rows={relations.data.map((r) => [<NameEditButton name={`${r.organization_name ?? 'Organización'}${r.organization_status === 'inactive' ? ' (inactiva)' : ''}`} onEdit={() => startEdit(r)} />, <span>{r.practitioner_name}{r.practitioner_status === 'inactive' ? ' (inactivo)' : ''}</span>, organizationPractitionerRoleLabel(r.role), <StatusBadge status={r.status} />, <StatusAction status={r.status} entityName={`${r.organization_name ?? 'Organización'} — ${r.practitioner_name ?? 'Profesional'}`} disabled={statusAction.isPending} onInactivate={() => statusAction.mutate(r)} onActivate={() => statusAction.mutate(r)} />])} /> : null}</SectionCard></div></>;
}
