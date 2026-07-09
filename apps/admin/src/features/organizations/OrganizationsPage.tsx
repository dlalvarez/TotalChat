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
  name: z.string().min(1, 'El nombre de la organización es obligatorio'),
  organization_type: z.string().min(1, 'Selecciona un tipo de organización'),
  legal_name: z.string().optional(),
  tax_id: z.string().optional(),
  email: z.string().email('Ingresa un correo válido').optional().or(z.literal('')),
  phone: z.string().optional(),
});

type FormValues = z.infer<typeof schema>;

const emptyToNull = (value?: string) => (value && value.trim().length > 0 ? value.trim() : null);

export function OrganizationsPage({ tenant }: { tenant: AdminTenant }) {
  const [showForm, setShowForm] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const queryClient = useQueryClient();
  const queryKey = useMemo(() => ['organizations', tenant.id], [tenant.id]);
  const organizations = useQuery({
    queryKey,
    queryFn: () => adminResourcesApi.listOrganizations(tenant.id),
  });

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { organization_type: 'clinic' },
  });

  const create = useMutation({
    mutationFn: (values: FormValues) =>
      adminResourcesApi.createOrganization(tenant.id, {
        name: values.name.trim(),
        organization_type: values.organization_type,
        legal_name: emptyToNull(values.legal_name),
        tax_id: emptyToNull(values.tax_id),
        email: emptyToNull(values.email),
        phone: emptyToNull(values.phone),
      }),
    onSuccess: async () => {
      setFeedback('Organización creada correctamente.');
      form.reset({ organization_type: 'clinic' });
      setShowForm(false);
      await queryClient.invalidateQueries({ queryKey });
    },
  });

  return (
    <>
      <PageHeader
        eyebrow="Fase 6B.1 · módulo funcional"
        title="Organizaciones"
        description="Gestiona organizaciones del tenant activo. Los identificadores técnicos viajan internamente; la tabla prioriza información legible."
        actions={<Button onClick={() => setShowForm((value) => !value)}>{showForm ? 'Cerrar formulario' : 'Crear organización'}</Button>}
      />

      {feedback ? <div className="mb-4 rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-sm font-medium text-emerald-800">{feedback}</div> : null}
      {create.isError ? <div className="mb-4"><ErrorState description={(create.error as Error).message} /></div> : null}

      {showForm ? (
        <SectionCard title="Nueva organización" description="Datos básicos para crear la organización en el backend.">
          <form className="grid gap-4 md:grid-cols-2" onSubmit={form.handleSubmit((values) => create.mutate(values))}>
            <FieldWrapper label="Nombre" error={form.formState.errors.name?.message}>
              <Input placeholder="Clínica Vida" {...form.register('name')} />
            </FieldWrapper>
            <FieldWrapper label="Tipo" error={form.formState.errors.organization_type?.message}>
              <Select {...form.register('organization_type')}>
                <option value="clinic">Clínica</option>
                <option value="medical_center">Centro médico</option>
                <option value="private_practice">Consultorio privado</option>
              </Select>
            </FieldWrapper>
            <FieldWrapper label="Razón social" error={form.formState.errors.legal_name?.message}>
              <Input {...form.register('legal_name')} />
            </FieldWrapper>
            <FieldWrapper label="NIT / identificación tributaria" error={form.formState.errors.tax_id?.message}>
              <Input {...form.register('tax_id')} />
            </FieldWrapper>
            <FieldWrapper label="Correo" error={form.formState.errors.email?.message}>
              <Input type="email" {...form.register('email')} />
            </FieldWrapper>
            <FieldWrapper label="Teléfono" error={form.formState.errors.phone?.message}>
              <Input {...form.register('phone')} />
            </FieldWrapper>
            <div className="md:col-span-2"><Button type="submit" disabled={create.isPending}>{create.isPending ? 'Creando…' : 'Guardar organización'}</Button></div>
          </form>
        </SectionCard>
      ) : null}

      <div className="mt-6">
        <SectionCard title="Listado de organizaciones" description={`Tenant activo: ${tenant.label}`}>
          {organizations.isLoading ? <LoadingState label="Cargando organizaciones…" /> : null}
          {organizations.isError ? <ErrorState description={(organizations.error as Error).message} /> : null}
          {organizations.isSuccess && organizations.data.length === 0 ? <EmptyState title="Sin organizaciones" description="Crea la primera organización para comenzar a configurar sedes." /> : null}
          {organizations.isSuccess && organizations.data.length > 0 ? (
            <DataTableShell columns={['Nombre', 'Tipo', 'Contacto', 'Estado']} rows={organizations.data.map((org) => [<strong>{org.name}</strong>, org.organization_type, org.email ?? org.phone ?? 'Sin contacto', <Badge tone={org.status === 'active' ? 'success' : 'neutral'}>{org.status === 'active' ? 'Activa' : 'Inactiva'}</Badge>])} />
          ) : null}
        </SectionCard>
      </div>
    </>
  );
}
