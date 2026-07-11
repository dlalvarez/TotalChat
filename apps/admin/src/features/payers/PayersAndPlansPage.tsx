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
import { adminResourcesApi, type Payer, type PayerPlan, type PayerType } from '../../api/adminResources';
import type { AdminTenant } from '../../config/tenant';
import { NameEditButton, StatusAction, StatusBadge } from '../adminResourceUtils';

const payerTypeSchema = z.object({ code: z.string().trim().min(1, 'Código requerido'), name: z.string().trim().min(1, 'Nombre requerido'), description: z.string().optional() });
const payerSchema = z.object({ payer_type_id: z.string().min(1, 'Selecciona un tipo activo'), name: z.string().trim().min(1, 'Nombre requerido'), description: z.string().optional() });
const planSchema = z.object({ payer_type_id: z.string().min(1, 'Selecciona un tipo activo'), payer_id: z.string().min(1, 'Selecciona un pagador activo'), name: z.string().trim().min(1, 'Nombre requerido'), description: z.string().optional() });

type PayerTypeForm = z.infer<typeof payerTypeSchema>;
type PayerForm = z.infer<typeof payerSchema>;
type PlanForm = z.infer<typeof planSchema>;

export function PayersAndPlansPage({ tenant }: { tenant: AdminTenant }) {
  const queryClient = useQueryClient();
  const [feedback, setFeedback] = useState<string | null>(null);
  const [editingType, setEditingType] = useState<PayerType | null>(null);
  const [editingPayer, setEditingPayer] = useState<Payer | null>(null);
  const [editingPlan, setEditingPlan] = useState<PayerPlan | null>(null);

  const payerTypesKey = useMemo(() => ['payer-types', tenant.id], [tenant.id]);
  const payersKey = useMemo(() => ['payers', tenant.id], [tenant.id]);
  const plansKey = useMemo(() => ['payer-plans', tenant.id], [tenant.id]);
  const payerTypes = useQuery({ queryKey: payerTypesKey, queryFn: () => adminResourcesApi.listPayerTypes(tenant.id) });
  const payers = useQuery({ queryKey: payersKey, queryFn: () => adminResourcesApi.listPayers(tenant.id) });
  const plans = useQuery({ queryKey: plansKey, queryFn: () => adminResourcesApi.listPayerPlans(tenant.id) });

  const activeTypes = (payerTypes.data ?? []).filter((type) => type.status === 'active');
  const activePayers = (payers.data ?? []).filter((payer) => payer.status === 'active' && payer.payer_type_status === 'active');

  const typeForm = useForm<PayerTypeForm>({ resolver: zodResolver(payerTypeSchema), defaultValues: { code: '', name: '', description: '' } });
  const payerForm = useForm<PayerForm>({ resolver: zodResolver(payerSchema), defaultValues: { payer_type_id: '', name: '', description: '' } });
  const planForm = useForm<PlanForm>({ resolver: zodResolver(planSchema), defaultValues: { payer_type_id: '', payer_id: '', name: '', description: '' } });
  const selectedPlanType = planForm.watch('payer_type_id');
  useEffect(() => { if (!editingPlan) planForm.setValue('payer_id', '', { shouldValidate: true }); }, [editingPlan, planForm, selectedPlanType]);
  const planPayers = activePayers.filter((payer) => payer.payer_type_id === selectedPlanType);

  const invalidateAll = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: payerTypesKey }),
      queryClient.invalidateQueries({ queryKey: payersKey }),
      queryClient.invalidateQueries({ queryKey: plansKey }),
    ]);
  };

  const saveType = useMutation({
    mutationFn: (values: PayerTypeForm) => editingType ? adminResourcesApi.updatePayerType(tenant.id, editingType.id, { ...values, description: values.description || null }) : adminResourcesApi.createPayerType(tenant.id, { ...values, description: values.description || null }),
    onSuccess: async () => { setFeedback(editingType ? 'Tipo de pagador actualizado.' : 'Tipo de pagador creado.'); setEditingType(null); typeForm.reset({ code: '', name: '', description: '' }); await invalidateAll(); },
  });
  const savePayer = useMutation({
    mutationFn: (values: PayerForm) => editingPayer ? adminResourcesApi.updatePayer(tenant.id, editingPayer.id, { name: values.name, description: values.description || null }) : adminResourcesApi.createPayer(tenant.id, { ...values, description: values.description || null }),
    onSuccess: async () => { setFeedback(editingPayer ? 'Pagador actualizado.' : 'Pagador creado.'); setEditingPayer(null); payerForm.reset({ payer_type_id: '', name: '', description: '' }); await invalidateAll(); },
  });
  const savePlan = useMutation({
    mutationFn: (values: PlanForm) => editingPlan ? adminResourcesApi.updatePayerPlan(tenant.id, editingPlan.id, { name: values.name, description: values.description || null }) : adminResourcesApi.createPayerPlan(tenant.id, { payer_id: values.payer_id, name: values.name, description: values.description || null }),
    onSuccess: async () => { setFeedback(editingPlan ? 'Plan actualizado.' : 'Plan creado.'); setEditingPlan(null); planForm.reset({ payer_type_id: '', payer_id: '', name: '', description: '' }); await invalidateAll(); },
  });
  const toggleType = useMutation({ mutationFn: (item: PayerType) => item.status === 'active' ? adminResourcesApi.disablePayerType(tenant.id, item.id) : adminResourcesApi.activatePayerType(tenant.id, item.id), onSuccess: invalidateAll });
  const togglePayer = useMutation({ mutationFn: (item: Payer) => item.status === 'active' ? adminResourcesApi.disablePayer(tenant.id, item.id) : adminResourcesApi.activatePayer(tenant.id, item.id), onSuccess: invalidateAll });
  const togglePlan = useMutation({ mutationFn: (item: PayerPlan) => item.status === 'active' ? adminResourcesApi.disablePayerPlan(tenant.id, item.id) : adminResourcesApi.activatePayerPlan(tenant.id, item.id), onSuccess: invalidateAll });
  const error = saveType.error ?? savePayer.error ?? savePlan.error ?? toggleType.error ?? togglePayer.error ?? togglePlan.error;

  return <>
    <PageHeader eyebrow="Fase 6B.7 · base comercial" title="Pagadores y planes" description="Administra Tipo de pagador → Pagador → Plan. Esta fase no configura precios ni tarifas." />
    {feedback ? <div className="mb-4 rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-sm font-medium text-emerald-800">{feedback}</div> : null}
    {error ? <div className="mb-4"><ErrorState description={(error as Error).message} /></div> : null}

    <div className="grid gap-6 xl:grid-cols-3">
      <SectionCard title="Tipos de pagador" description="Código único, nombre y estado lógico.">
        <form className="mb-4 grid gap-3" onSubmit={typeForm.handleSubmit((values) => saveType.mutate(values))}>
          <FieldWrapper label="Código *" error={typeForm.formState.errors.code?.message}><Input {...typeForm.register('code')} placeholder="prepaid_medicine" /></FieldWrapper>
          <FieldWrapper label="Nombre *" error={typeForm.formState.errors.name?.message}><Input {...typeForm.register('name')} placeholder="Medicina prepagada" /></FieldWrapper>
          <FieldWrapper label="Descripción"><Input {...typeForm.register('description')} /></FieldWrapper>
          <Button type="submit" disabled={saveType.isPending}>{editingType ? 'Guardar tipo' : 'Crear tipo'}</Button>
        </form>
        {payerTypes.isLoading ? <LoadingState /> : null}
        {payerTypes.isSuccess && payerTypes.data.length === 0 ? <EmptyState title="Sin tipos de pagador" description="Crea al menos un tipo activo para habilitar pagadores." /> : null}
        {payerTypes.isSuccess && payerTypes.data.length > 0 ? <DataTableShell columns={['Tipo', 'Código', 'Estado', 'Acción']} rows={payerTypes.data.map((type) => [<NameEditButton name={type.name} onEdit={() => { setEditingType(type); typeForm.reset({ code: type.code, name: type.name, description: type.description ?? '' }); }} />, type.code, <StatusBadge status={type.status} />, <StatusAction status={type.status} entityName={type.name} disabled={toggleType.isPending} onInactivate={() => toggleType.mutate(type)} onActivate={() => toggleType.mutate(type)} />])} /> : null}
      </SectionCard>

      <SectionCard title="Pagadores" description="Entidad o categoría comercial bajo un tipo activo.">
        <form className="mb-4 grid gap-3" onSubmit={payerForm.handleSubmit((values) => savePayer.mutate(values))}>
          <FieldWrapper label="Tipo de pagador activo *" error={payerForm.formState.errors.payer_type_id?.message} hint={activeTypes.length === 0 ? 'No hay tipos activos disponibles.' : undefined}><Select {...payerForm.register('payer_type_id')} disabled={Boolean(editingPayer)}><option value="">Selecciona un tipo</option>{(editingPayer ? payerTypes.data ?? [] : activeTypes).map((type) => <option key={type.id} value={type.id}>{type.name}</option>)}</Select></FieldWrapper>
          <FieldWrapper label="Nombre *" error={payerForm.formState.errors.name?.message}><Input {...payerForm.register('name')} placeholder="Particular" /></FieldWrapper>
          <FieldWrapper label="Descripción"><Input {...payerForm.register('description')} /></FieldWrapper>
          <Button type="submit" disabled={savePayer.isPending || (!editingPayer && activeTypes.length === 0)}>{editingPayer ? 'Guardar pagador' : 'Crear pagador'}</Button>
        </form>
        {payers.isSuccess && payers.data.length > 0 ? <DataTableShell columns={['Pagador', 'Tipo', 'Estado', 'Acción']} rows={payers.data.map((payer) => [<NameEditButton name={payer.name} onEdit={() => { setEditingPayer(payer); payerForm.reset({ payer_type_id: payer.payer_type_id, name: payer.name, description: payer.description ?? '' }); }} />, `${payer.payer_type_name ?? 'Tipo'}${payer.payer_type_status === 'inactive' ? ' (inactivo)' : ''}`, <StatusBadge status={payer.status} />, <StatusAction status={payer.status} entityName={payer.name} disabled={togglePayer.isPending} onInactivate={() => togglePayer.mutate(payer)} onActivate={() => togglePayer.mutate(payer)} />])} /> : <EmptyState title="Sin pagadores" description="Crea pagadores cuando exista un tipo activo." />}
      </SectionCard>

      <SectionCard title="Planes" description="Producto, convenio o variante comercial del pagador. Sin precios.">
        <form className="mb-4 grid gap-3" onSubmit={planForm.handleSubmit((values) => savePlan.mutate(values))}>
          <FieldWrapper label="Tipo de pagador activo *" error={planForm.formState.errors.payer_type_id?.message}><Select {...planForm.register('payer_type_id')} disabled={Boolean(editingPlan)}><option value="">Selecciona un tipo</option>{(editingPlan ? payerTypes.data ?? [] : activeTypes).map((type) => <option key={type.id} value={type.id}>{type.name}</option>)}</Select></FieldWrapper>
          <FieldWrapper label="Pagador activo *" error={planForm.formState.errors.payer_id?.message} hint={!editingPlan && selectedPlanType && planPayers.length === 0 ? 'No hay pagadores activos para este tipo.' : undefined}><Select {...planForm.register('payer_id')} disabled={Boolean(editingPlan) || !selectedPlanType}><option value="">Selecciona un pagador</option>{(editingPlan ? payers.data ?? [] : planPayers).map((payer) => <option key={payer.id} value={payer.id}>{payer.name}</option>)}</Select></FieldWrapper>
          <FieldWrapper label="Nombre *" error={planForm.formState.errors.name?.message}><Input {...planForm.register('name')} placeholder="Tarifa particular estándar" /></FieldWrapper>
          <FieldWrapper label="Descripción"><Input {...planForm.register('description')} /></FieldWrapper>
          <Button type="submit" disabled={savePlan.isPending || (!editingPlan && planPayers.length === 0)}>{editingPlan ? 'Guardar plan' : 'Crear plan'}</Button>
        </form>
        {plans.isSuccess && plans.data.length > 0 ? <DataTableShell columns={['Plan', 'Pagador', 'Tipo', 'Estado', 'Acción']} rows={plans.data.map((plan) => [<NameEditButton name={plan.name} onEdit={() => { setEditingPlan(plan); planForm.reset({ payer_type_id: plan.payer_type_id ?? '', payer_id: plan.payer_id, name: plan.name, description: plan.description ?? '' }); }} />, `${plan.payer_name ?? 'Pagador'}${plan.payer_status === 'inactive' ? ' (inactivo)' : ''}`, `${plan.payer_type_name ?? 'Tipo'}${plan.payer_type_status === 'inactive' ? ' (inactivo)' : ''}`, <StatusBadge status={plan.status} />, <StatusAction status={plan.status} entityName={plan.name} disabled={togglePlan.isPending} onInactivate={() => togglePlan.mutate(plan)} onActivate={() => togglePlan.mutate(plan)} />])} /> : <EmptyState title="Sin planes" description="Crea planes cuando existan pagadores activos." />}
      </SectionCard>
    </div>
  </>;
}
