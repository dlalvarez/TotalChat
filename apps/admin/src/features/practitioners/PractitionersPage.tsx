import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { PageHeader } from '../../components/layout/PageHeader';
import { Button } from '../../components/ui/Button';
import { SectionCard } from '../../components/ui/Card';
import { DataTableShell } from '../../components/ui/DataTable';
import { FieldWrapper, Input } from '../../components/ui/Form';
import { EmptyState, ErrorState, LoadingState } from '../../components/ui/States';
import { adminResourcesApi, type Practitioner } from '../../api/adminResources';
import type { AdminTenant } from '../../config/tenant';
import { RowActions, StatusBadge } from '../adminResourceUtils';
import { emptyToNull } from '../adminResourceFormat';

const schema = z.object({ full_name: z.string().min(1, 'El nombre completo es obligatorio'), professional_type: z.string().optional(), professional_license: z.string().optional(), email: z.string().email('Ingresa un correo válido').or(z.literal('')).optional(), phone: z.string().optional() });
type FormValues = z.infer<typeof schema>;
const defaults = (p?: Practitioner): FormValues => ({ full_name: p?.full_name ?? '', professional_type: p?.professional_type ?? '', professional_license: p?.professional_license ?? '', email: p?.email ?? '', phone: p?.phone ?? '' });

export function PractitionersPage({ tenant }: { tenant: AdminTenant }) {
  const [showForm, setShowForm] = useState(false); const [editing, setEditing] = useState<Practitioner | null>(null); const [feedback, setFeedback] = useState<string | null>(null);
  const queryClient = useQueryClient(); const practitionersKey = useMemo(() => ['practitioners', tenant.id], [tenant.id]);
  const practitioners = useQuery({ queryKey: practitionersKey, queryFn: () => adminResourcesApi.listPractitioners(tenant.id) });
  const form = useForm<FormValues>({ resolver: zodResolver(schema), defaultValues: defaults() });
  const payload = (v: FormValues) => ({ full_name: v.full_name.trim(), professional_type: emptyToNull(v.professional_type), professional_license: emptyToNull(v.professional_license), email: emptyToNull(v.email), phone: emptyToNull(v.phone) });
  const closeForm = () => { setEditing(null); setShowForm(false); form.reset(defaults()); };
  const save = useMutation({ mutationFn: (v: FormValues) => editing ? adminResourcesApi.updatePractitioner(tenant.id, editing.id, payload(v)) : adminResourcesApi.createPractitioner(tenant.id, payload(v)), onSuccess: async () => { setFeedback(editing ? 'Profesional actualizado correctamente.' : 'Profesional creado correctamente.'); closeForm(); await queryClient.invalidateQueries({ queryKey: practitionersKey }); } });
  const disable = useMutation({ mutationFn: (p: Practitioner) => adminResourcesApi.disablePractitioner(tenant.id, p.id), onSuccess: async () => { setFeedback('Profesional inactivado correctamente.'); await queryClient.invalidateQueries({ queryKey: practitionersKey }); } });
  const startEdit = (p: Practitioner) => { setEditing(p); form.reset(defaults(p)); setShowForm(true); };
  return <><PageHeader eyebrow="Fase 6B.3 · edición e inactivación" title="Profesionales" description="Gestiona profesionales. Especialidades y servicios permanecen diferidos." actions={<Button onClick={() => showForm ? closeForm() : setShowForm(true)}>{showForm ? 'Cerrar formulario' : 'Crear profesional'}</Button>} />
    {feedback ? <div className="mb-4 rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-sm font-medium text-emerald-800">{feedback}</div> : null}{save.isError ? <div className="mb-4"><ErrorState description={(save.error as Error).message} /></div> : null}{disable.isError ? <div className="mb-4"><ErrorState description={(disable.error as Error).message} /></div> : null}
    {showForm ? <SectionCard title={editing ? `Editar ${editing.full_name}` : 'Nuevo profesional'} description="Registra o actualiza datos básicos del profesional."><form className="grid gap-4 md:grid-cols-2" onSubmit={form.handleSubmit((v) => save.mutate(v))}>
      <FieldWrapper label="Nombre completo" error={form.formState.errors.full_name?.message}><Input placeholder="Dra. Ana Pérez" {...form.register('full_name')} /></FieldWrapper><FieldWrapper label="Tipo profesional" error={form.formState.errors.professional_type?.message}><Input placeholder="Médico general" {...form.register('professional_type')} /></FieldWrapper><FieldWrapper label="Registro / licencia profesional" error={form.formState.errors.professional_license?.message}><Input placeholder="RM 123456" {...form.register('professional_license')} /></FieldWrapper><FieldWrapper label="Correo" error={form.formState.errors.email?.message}><Input type="email" placeholder="profesional@clinica.com" {...form.register('email')} /></FieldWrapper><FieldWrapper label="Teléfono" error={form.formState.errors.phone?.message}><Input placeholder="+57 300 000 0000" {...form.register('phone')} /></FieldWrapper><div className="flex gap-2 md:col-span-2"><Button type="submit" disabled={save.isPending}>{save.isPending ? 'Guardando…' : 'Guardar cambios'}</Button>{editing ? <Button type="button" variant="secondary" onClick={closeForm}>Cancelar</Button> : null}</div>
    </form></SectionCard> : null}
    <div className="mt-6"><SectionCard title="Listado de profesionales" description={`Tenant activo: ${tenant.label}`}>{practitioners.isLoading ? <LoadingState label="Cargando profesionales…" /> : null}{practitioners.isError ? <ErrorState description={(practitioners.error as Error).message} /> : null}{practitioners.isSuccess && practitioners.data.length === 0 ? <EmptyState title="Sin profesionales" description="Crea el primer profesional con datos básicos." /> : null}{practitioners.isSuccess && practitioners.data.length > 0 ? <DataTableShell columns={['Profesional', 'Tipo', 'Registro', 'Contacto', 'Estado', 'Acciones']} rows={practitioners.data.map((p) => [<strong>{p.full_name}</strong>, p.professional_type ?? 'Sin tipo', p.professional_license ?? 'Sin registro', p.email ?? p.phone ?? 'Sin contacto', <StatusBadge status={p.status} />, <RowActions disabled={p.status !== 'active' || disable.isPending} onEdit={() => startEdit(p)} onDisable={() => { if (window.confirm(`¿Inactivar a ${p.full_name}? No se eliminará físicamente.`)) disable.mutate(p); }} />])} /> : null}</SectionCard></div>
  </>;
}
