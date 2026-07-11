import { useEffect, useMemo, useState } from 'react';
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
import { adminResourcesApi, type PractitionerServicePrice } from '../../api/adminResources';
import type { AdminTenant } from '../../config/tenant';
import { NameEditButton, StatusAction, StatusBadge } from '../adminResourceUtils';

const OPERATIVE_CURRENCY = 'COP' as const;

const schema = z.object({
  organization_id: z.string().min(1, 'Selecciona una organización'),
  practitioner_id: z.string().min(1, 'Selecciona un profesional'),
  practitioner_service_id: z.string().min(1, 'Selecciona un servicio'),
  payer_type_id: z.string().min(1, 'Selecciona un tipo de pagador'),
  payer_id: z.string().min(1, 'Selecciona un pagador'),
  payer_plan_id: z.string().min(1, 'Selecciona un plan'),
  price: z.coerce.number().min(0, 'El precio debe ser mayor o igual a 0'),
  valid_from: z.string().min(1, 'Selecciona vigencia desde'),
  valid_to: z.string().optional(),
  status: z.enum(['active', 'inactive']).default('active'),
});
type FormValues = z.infer<typeof schema>;

const defaults = (price?: PractitionerServicePrice): FormValues => ({
  organization_id: price?.organization_id ?? '',
  practitioner_id: price?.practitioner_id ?? '',
  practitioner_service_id: price?.practitioner_service_id ?? '',
  payer_type_id: price?.payer_type_id ?? '',
  payer_id: price?.payer_id ?? '',
  payer_plan_id: price?.payer_plan_id ?? '',
  price: price?.price ?? 0,
  valid_from: price?.valid_from ?? '',
  valid_to: price?.valid_to ?? '',
  status: price?.status === 'inactive' ? 'inactive' : 'active',
});

export function PricesPage({ tenant }: { tenant: AdminTenant }) {
  const [editing, setEditing] = useState<PractitionerServicePrice | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const queryClient = useQueryClient();
  const pricesKey = useMemo(() => ['practitioner-service-prices', tenant.id], [tenant.id]);
  const prices = useQuery({ queryKey: pricesKey, queryFn: () => adminResourcesApi.listPractitionerServicePrices(tenant.id) });
  const organizations = useQuery({ queryKey: ['organizations', tenant.id], queryFn: () => adminResourcesApi.listOrganizations(tenant.id) });
  const relations = useQuery({ queryKey: ['organization-practitioners', tenant.id], queryFn: () => adminResourcesApi.listOrganizationPractitioners(tenant.id) });
  const services = useQuery({ queryKey: ['practitioner-services', tenant.id], queryFn: () => adminResourcesApi.listPractitionerServices(tenant.id) });
  const payerTypes = useQuery({ queryKey: ['payer-types', tenant.id], queryFn: () => adminResourcesApi.listPayerTypes(tenant.id) });
  const payers = useQuery({ queryKey: ['payers', tenant.id], queryFn: () => adminResourcesApi.listPayers(tenant.id) });
  const plans = useQuery({ queryKey: ['payer-plans', tenant.id], queryFn: () => adminResourcesApi.listPayerPlans(tenant.id) });
  const form = useForm<FormValues>({ resolver: zodResolver(schema), defaultValues: defaults() });

  const organizationId = form.watch('organization_id');
  const practitionerId = form.watch('practitioner_id');
  const payerTypeId = form.watch('payer_type_id');
  const payerId = form.watch('payer_id');

  useEffect(() => { if (!editing) { form.setValue('practitioner_id', ''); form.setValue('practitioner_service_id', ''); } }, [organizationId]);
  useEffect(() => { if (!editing) form.setValue('practitioner_service_id', ''); }, [practitionerId]);
  useEffect(() => { if (!editing) { form.setValue('payer_id', ''); form.setValue('payer_plan_id', ''); } }, [payerTypeId]);
  useEffect(() => { if (!editing) form.setValue('payer_plan_id', ''); }, [payerId]);

  const activeOrganizations = (organizations.data ?? []).filter((item) => item.status === 'active');
  const activeRelations = (relations.data ?? []).filter((item) => item.status === 'active' && item.organization_status === 'active' && item.practitioner_status === 'active');
  const practitionerOptions = activeRelations.filter((item) => item.organization_id === organizationId);
  const serviceOptions = (services.data ?? []).filter((item) => item.status === 'active' && item.organization_id === organizationId && item.practitioner_id === practitionerId);
  const payerTypeOptions = (payerTypes.data ?? []).filter((item) => item.status === 'active');
  const payerOptions = (payers.data ?? []).filter((item) => item.status === 'active' && item.payer_type_status === 'active' && item.payer_type_id === payerTypeId);
  const planOptions = (plans.data ?? []).filter((item) => item.status === 'active' && item.payer_status === 'active' && item.payer_type_status === 'active' && item.payer_id === payerId);

  const save = useMutation({
    mutationFn: (values: FormValues) => editing
      ? adminResourcesApi.updatePractitionerServicePrice(tenant.id, editing.id, { price: values.price, valid_from: values.valid_from, valid_to: values.valid_to || null, status: values.status })
      : adminResourcesApi.createPractitionerServicePrice(tenant.id, { practitioner_service_id: values.practitioner_service_id, payer_plan_id: values.payer_plan_id, price: values.price, currency: OPERATIVE_CURRENCY, valid_from: values.valid_from, valid_to: values.valid_to || null }),
    onSuccess: async () => { setFeedback(editing ? 'Precio actualizado correctamente.' : 'Precio creado correctamente con moneda operativa COP.'); setEditing(null); form.reset(defaults()); await queryClient.invalidateQueries({ queryKey: pricesKey }); },
  });
  const statusAction = useMutation({
    mutationFn: (price: PractitionerServicePrice) => price.status === 'active' ? adminResourcesApi.disablePractitionerServicePrice(tenant.id, price.id) : adminResourcesApi.activatePractitionerServicePrice(tenant.id, price.id),
    onSuccess: async () => { await queryClient.invalidateQueries({ queryKey: pricesKey }); },
  });
  const startEdit = (price: PractitionerServicePrice) => { setEditing(price); form.reset(defaults(price)); };
  const cancelEdit = () => { setEditing(null); form.reset(defaults()); };

  return <>
    <PageHeader eyebrow="Fase 6B.8 · precios y tarifas" title="Precios" description="Administra Servicio del profesional + Plan del pagador = Precio. Moneda operativa temporal: COP." />
    {feedback ? <div className="mb-4 rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-sm font-medium text-emerald-800">{feedback}</div> : null}
    {save.isError ? <div className="mb-4"><ErrorState description={(save.error as Error).message} /></div> : null}
    {statusAction.isError ? <div className="mb-4"><ErrorState description={(statusAction.error as Error).message} /></div> : null}

    <SectionCard title={editing ? 'Editar precio' : 'Nuevo precio'} description={editing ? 'Servicio, plan y moneda quedan bloqueados; inactiva y crea otro si hubo error.' : 'Selecciona datos activos. COP se envía automáticamente; no hay selector de moneda por precio.'}>
      <form className="grid gap-4 md:grid-cols-3" onSubmit={form.handleSubmit((values) => save.mutate(values))}>
        <FieldWrapper label="Organización *"><Select {...form.register('organization_id')} disabled={Boolean(editing)}><option value="">Selecciona</option>{(editing ? organizations.data ?? [] : activeOrganizations).map((o) => <option key={o.id} value={o.id}>{o.name}</option>)}</Select></FieldWrapper>
        <FieldWrapper label="Profesional *"><Select {...form.register('practitioner_id')} disabled={Boolean(editing) || !organizationId}><option value="">Selecciona</option>{(editing ? [{ practitioner_id: editing.practitioner_id ?? '', practitioner_name: editing.practitioner_name }] : practitionerOptions).map((p) => <option key={p.practitioner_id} value={p.practitioner_id}>{p.practitioner_name}</option>)}</Select></FieldWrapper>
        <FieldWrapper label="Servicio *"><Select {...form.register('practitioner_service_id')} disabled={Boolean(editing) || !practitionerId}><option value="">Selecciona</option>{(editing ? [{ id: editing.practitioner_service_id, name: editing.practitioner_service_name }] : serviceOptions).map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}</Select></FieldWrapper>
        <FieldWrapper label="Tipo de pagador *"><Select {...form.register('payer_type_id')} disabled={Boolean(editing)}><option value="">Selecciona</option>{(editing ? payerTypes.data ?? [] : payerTypeOptions).map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}</Select></FieldWrapper>
        <FieldWrapper label="Pagador *"><Select {...form.register('payer_id')} disabled={Boolean(editing) || !payerTypeId}><option value="">Selecciona</option>{(editing ? [{ id: editing.payer_id ?? '', name: editing.payer_name }] : payerOptions).map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}</Select></FieldWrapper>
        <FieldWrapper label="Plan *"><Select {...form.register('payer_plan_id')} disabled={Boolean(editing) || !payerId}><option value="">Selecciona</option>{(editing ? [{ id: editing.payer_plan_id, name: editing.payer_plan_name }] : planOptions).map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}</Select></FieldWrapper>
        <FieldWrapper label="Precio *" error={form.formState.errors.price?.message}><Input type="number" min="0" step="0.01" {...form.register('price')} /></FieldWrapper>
        <FieldWrapper label="Moneda operativa"><div className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm font-semibold text-slate-700">{OPERATIVE_CURRENCY} · no editable en esta fase</div></FieldWrapper>
        <FieldWrapper label="Vigencia desde *" error={form.formState.errors.valid_from?.message}><Input type="date" {...form.register('valid_from')} /></FieldWrapper>
        <FieldWrapper label="Vigencia hasta"><Input type="date" {...form.register('valid_to')} /></FieldWrapper>
        {editing ? <FieldWrapper label="Estado"><Select {...form.register('status')}><option value="active">Activo</option><option value="inactive">Inactivo</option></Select></FieldWrapper> : null}
        <div className="flex gap-2 md:col-span-3"><Button type="submit" disabled={save.isPending}>{save.isPending ? 'Guardando…' : 'Guardar precio'}</Button>{editing ? <Button type="button" variant="secondary" onClick={cancelEdit}>Cancelar</Button> : null}</div>
      </form>
    </SectionCard>

    <div className="mt-6"><SectionCard title="Precios configurados" description="Listado con nombres legibles; los UUIDs permanecen internos.">
      {prices.isLoading ? <LoadingState label="Cargando precios…" /> : null}
      {prices.isError ? <ErrorState description={(prices.error as Error).message} /> : null}
      {prices.isSuccess && prices.data.length === 0 ? <EmptyState title="Sin precios" description="Configura la primera tarifa manual por servicio y plan." /> : null}
      {prices.isSuccess && prices.data.length > 0 ? <DataTableShell columns={['Servicio', 'Plan', 'Precio', 'Vigencia', 'Estado', 'Acciones']} rows={prices.data.map((price) => [
        <NameEditButton name={`${price.practitioner_service_name ?? 'Servicio'} · ${price.practitioner_name ?? 'Profesional'}`} onEdit={() => startEdit(price)} />,
        <span>{price.payer_type_name} · {price.payer_name} · {price.payer_plan_name}</span>,
        `${price.price} ${price.currency}`,
        `${price.valid_from}${price.valid_to ? ` → ${price.valid_to}` : ' → abierta'}`,
        <StatusBadge status={price.status} />,
        <StatusAction status={price.status} entityName={price.practitioner_service_name ?? 'precio'} disabled={statusAction.isPending} onInactivate={() => statusAction.mutate(price)} onActivate={() => statusAction.mutate(price)} />,
      ])} /> : null}
    </SectionCard></div>
  </>;
}
