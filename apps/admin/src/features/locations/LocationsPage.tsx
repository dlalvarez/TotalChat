import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { PageHeader } from '../../components/layout/PageHeader';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { SectionCard } from '../../components/ui/Card';
import { DataTableShell } from '../../components/ui/DataTable';
import { FieldWrapper, Input, Select } from '../../components/ui/Form';
import { EmptyState, ErrorState, LoadingState } from '../../components/ui/States';
import { adminResourcesApi } from '../../api/adminResources';
import type { AdminTenant } from '../../config/tenant';

const schema = z.object({
  organization_id: z.string().min(1, 'Selecciona una organización'),
  name: z.string().min(1, 'El nombre de la sede es obligatorio'),
  address: z.string().optional(),
  city: z.string().optional(),
  neighborhood: z.string().optional(),
  reference: z.string().optional(),
  is_virtual: z.boolean().default(false),
});

type FormValues = z.infer<typeof schema>;
const emptyToNull = (value?: string) => (value && value.trim().length > 0 ? value.trim() : null);

export function LocationsPage({ tenant }: { tenant: AdminTenant }) {
  const [showForm, setShowForm] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const queryClient = useQueryClient();
  const locationsKey = useMemo(() => ['locations', tenant.id], [tenant.id]);
  const organizationsKey = useMemo(() => ['organizations', tenant.id], [tenant.id]);

  const locations = useQuery({ queryKey: locationsKey, queryFn: () => adminResourcesApi.listLocations(tenant.id) });
  const organizations = useQuery({ queryKey: organizationsKey, queryFn: () => adminResourcesApi.listOrganizations(tenant.id) });
  const organizationNames = new Map((organizations.data ?? []).map((org) => [org.id, org.name]));

  const form = useForm<FormValues>({ resolver: zodResolver(schema), defaultValues: { is_virtual: false } });

  const create = useMutation({
    mutationFn: (values: FormValues) =>
      adminResourcesApi.createLocation(tenant.id, {
        organization_id: values.organization_id,
        name: values.name.trim(),
        address: emptyToNull(values.address),
        city: emptyToNull(values.city),
        neighborhood: emptyToNull(values.neighborhood),
        reference: emptyToNull(values.reference),
        is_virtual: values.is_virtual,
      }),
    onSuccess: async () => {
      setFeedback('Sede creada correctamente.');
      form.reset({ is_virtual: false });
      setShowForm(false);
      await queryClient.invalidateQueries({ queryKey: locationsKey });
    },
  });

  return (
    <>
      <PageHeader
        eyebrow="Fase 6B.1 · módulo funcional"
        title="Sedes"
        description="Gestiona sedes físicas o virtuales. La organización se selecciona por nombre y su UUID permanece interno."
        actions={<Button onClick={() => setShowForm((value) => !value)}>{showForm ? 'Cerrar formulario' : 'Crear sede'}</Button>}
      />

      {feedback ? <div className="mb-4 rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-sm font-medium text-emerald-800">{feedback}</div> : null}
      {create.isError ? <div className="mb-4"><ErrorState description={(create.error as Error).message} /></div> : null}

      {showForm ? (
        <SectionCard title="Nueva sede" description="Selecciona una organización por nombre y registra los datos operativos visibles para el administrador.">
          <form className="grid gap-4 md:grid-cols-2" onSubmit={form.handleSubmit((values) => create.mutate(values))}>
            <FieldWrapper label="Organización" hint="Selector amigable; el identificador técnico queda interno." error={form.formState.errors.organization_id?.message}>
              <Select {...form.register('organization_id')} disabled={organizations.isLoading || (organizations.data?.length ?? 0) === 0}>
                <option value="">Selecciona una organización</option>
                {(organizations.data ?? []).map((org) => <option key={org.id} value={org.id}>{org.name}</option>)}
              </Select>
            </FieldWrapper>
            <FieldWrapper label="Nombre de la sede" error={form.formState.errors.name?.message}>
              <Input placeholder="Sede Norte" {...form.register('name')} />
            </FieldWrapper>
            <FieldWrapper label="Dirección" error={form.formState.errors.address?.message}>
              <Input {...form.register('address')} />
            </FieldWrapper>
            <FieldWrapper label="Ciudad" error={form.formState.errors.city?.message}>
              <Input {...form.register('city')} />
            </FieldWrapper>
            <FieldWrapper label="Barrio / zona" error={form.formState.errors.neighborhood?.message}>
              <Input {...form.register('neighborhood')} />
            </FieldWrapper>
            <FieldWrapper label="Referencia" error={form.formState.errors.reference?.message}>
              <Input {...form.register('reference')} />
            </FieldWrapper>
            <label className="flex items-center gap-3 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700 md:col-span-2">
              <input type="checkbox" className="h-4 w-4 rounded border-slate-300" {...form.register('is_virtual')} />
              Es una sede virtual
            </label>
            <div className="md:col-span-2"><Button type="submit" disabled={create.isPending || (organizations.data?.length ?? 0) === 0}>{create.isPending ? 'Creando…' : 'Guardar sede'}</Button></div>
          </form>
        </SectionCard>
      ) : null}

      <div className="mt-6">
        <SectionCard title="Listado de sedes" description={`Tenant activo: ${tenant.label}`}>
          {locations.isLoading ? <LoadingState label="Cargando sedes…" /> : null}
          {locations.isError ? <ErrorState description={(locations.error as Error).message} /> : null}
          {locations.isSuccess && locations.data.length === 0 ? <EmptyState title="Sin sedes" description="Crea la primera sede usando una organización existente." /> : null}
          {locations.isSuccess && locations.data.length > 0 ? (
            <DataTableShell columns={['Sede', 'Organización', 'Ubicación', 'Tipo', 'Estado']} rows={locations.data.map((location) => [<strong>{location.name}</strong>, organizationNames.get(location.organization_id) ?? 'Organización no disponible', [location.city, location.address].filter(Boolean).join(' · ') || 'Sin ubicación', <Badge tone={location.is_virtual ? 'info' : 'neutral'}>{location.is_virtual ? 'Virtual' : 'Presencial'}</Badge>, <Badge tone={location.status === 'active' ? 'success' : 'neutral'}>{location.status === 'active' ? 'Activa' : 'Inactiva'}</Badge>])} />
          ) : null}
        </SectionCard>
      </div>
    </>
  );
}
