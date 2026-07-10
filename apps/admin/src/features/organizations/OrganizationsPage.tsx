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
import { adminResourcesApi, type Organization } from '../../api/adminResources';
import type { AdminTenant } from '../../config/tenant';
import { emptyToNull } from '../adminResourceFormat';
import { NameEditButton, StatusAction, StatusBadge } from '../adminResourceUtils';

const schema = z.object({
  name: z.string().min(1, 'El nombre de la organización es obligatorio'),
  organization_type: z.string().min(1, 'Selecciona un tipo de organización'),
  legal_name: z.string().optional(),
  tax_id: z.string().optional(),
  email: z.string().email('Ingresa un correo válido').optional().or(z.literal('')),
  phone: z.string().optional(),
});

type FormValues = z.infer<typeof schema>;

function formDefaults(organization?: Organization): FormValues {
  return {
    name: organization?.name ?? '',
    organization_type: organization?.organization_type ?? 'clinic',
    legal_name: organization?.legal_name ?? '',
    tax_id: organization?.tax_id ?? '',
    email: organization?.email ?? '',
    phone: organization?.phone ?? '',
  };
}

function toPayload(values: FormValues) {
  return {
    name: values.name.trim(),
    organization_type: values.organization_type,
    legal_name: emptyToNull(values.legal_name),
    tax_id: emptyToNull(values.tax_id),
    email: emptyToNull(values.email),
    phone: emptyToNull(values.phone),
  };
}

export function OrganizationsPage({ tenant }: { tenant: AdminTenant }) {
  const [editing, setEditing] = useState<Organization | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const queryClient = useQueryClient();
  const queryKey = useMemo(() => ['organizations', tenant.id], [tenant.id]);

  const organizations = useQuery({
    queryKey,
    queryFn: () => adminResourcesApi.listOrganizations(tenant.id),
  });

  const form = useForm<FormValues>({ resolver: zodResolver(schema), defaultValues: formDefaults() });

  const closeForm = () => {
    setEditing(null);
    setShowForm(false);
    form.reset(formDefaults());
  };

  const save = useMutation({
    mutationFn: (values: FormValues) =>
      editing
        ? adminResourcesApi.updateOrganization(tenant.id, editing.id, toPayload(values))
        : adminResourcesApi.createOrganization(tenant.id, toPayload(values)),
    onSuccess: async () => {
      setFeedback(editing ? 'Organización actualizada correctamente.' : 'Organización creada correctamente.');
      closeForm();
      await queryClient.invalidateQueries({ queryKey });
    },
  });

  const toggleStatus = useMutation({
    mutationFn: (organization: Organization) =>
      organization.status === 'active'
        ? adminResourcesApi.disableOrganization(tenant.id, organization.id)
        : adminResourcesApi.activateOrganization(tenant.id, organization.id),
    onSuccess: async (organization) => {
      setFeedback(organization.status === 'active' ? 'Organización activada correctamente.' : 'Organización inactivada correctamente.');
      await queryClient.invalidateQueries({ queryKey });
    },
  });

  const startEdit = (organization: Organization) => {
    setEditing(organization);
    form.reset(formDefaults(organization));
    setShowForm(true);
  };

  return (
    <>
      <PageHeader
        eyebrow="Fase 6B.3 · edición e inactivación"
        title="Organizaciones"
        description="Gestiona organizaciones del tenant activo sin exponer identificadores técnicos."
        actions={<Button onClick={() => (showForm ? closeForm() : setShowForm(true))}>{showForm ? 'Cerrar formulario' : 'Crear organización'}</Button>}
      />

      {feedback ? <div className="mb-4 rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-sm font-medium text-emerald-800">{feedback}</div> : null}
      {save.isError ? <div className="mb-4"><ErrorState description={(save.error as Error).message} /></div> : null}
      {toggleStatus.isError ? <div className="mb-4"><ErrorState description={(toggleStatus.error as Error).message} /></div> : null}

      {showForm ? (
        <SectionCard title={editing ? `Editar ${editing.name}` : 'Nueva organización'} description="Actualiza datos básicos. El estado se controla con la acción Inactivar o Activar.">
          <form className="grid gap-4 md:grid-cols-2" onSubmit={form.handleSubmit((values) => save.mutate(values))}>
            <FieldWrapper label="Nombre" error={form.formState.errors.name?.message}><Input placeholder="Clínica Vida" {...form.register('name')} /></FieldWrapper>
            <FieldWrapper label="Tipo" error={form.formState.errors.organization_type?.message}>
              <Select {...form.register('organization_type')}>
                <option value="clinic">Clínica</option>
                <option value="medical_center">Centro médico</option>
                <option value="private_practice">Consultorio privado</option>
              </Select>
            </FieldWrapper>
            <FieldWrapper label="Razón social" error={form.formState.errors.legal_name?.message}><Input {...form.register('legal_name')} /></FieldWrapper>
            <FieldWrapper label="NIT / identificación tributaria" error={form.formState.errors.tax_id?.message}><Input {...form.register('tax_id')} /></FieldWrapper>
            <FieldWrapper label="Correo" error={form.formState.errors.email?.message}><Input type="email" {...form.register('email')} /></FieldWrapper>
            <FieldWrapper label="Teléfono" error={form.formState.errors.phone?.message}><Input {...form.register('phone')} /></FieldWrapper>
            <div className="flex gap-2 md:col-span-2">
              <Button type="submit" disabled={save.isPending}>{save.isPending ? 'Guardando…' : 'Guardar cambios'}</Button>
              {editing ? <Button type="button" variant="secondary" onClick={closeForm}>Cancelar</Button> : null}
            </div>
          </form>
        </SectionCard>
      ) : null}

      <div className="mt-6">
        <SectionCard title="Listado de organizaciones" description={`Tenant activo: ${tenant.label}`}>
          {organizations.isLoading ? <LoadingState label="Cargando organizaciones…" /> : null}
          {organizations.isError ? <ErrorState description={(organizations.error as Error).message} /> : null}
          {organizations.isSuccess && organizations.data.length === 0 ? <EmptyState title="Sin organizaciones" description="Crea la primera organización para comenzar a configurar sedes." /> : null}
          {organizations.isSuccess && organizations.data.length > 0 ? (
            <DataTableShell
              columns={['Nombre', 'Tipo', 'Contacto', 'Estado', 'Acciones']}
              rows={organizations.data.map((organization) => [
                <NameEditButton onClick={() => startEdit(organization)}>{organization.name}</NameEditButton>,
                organization.organization_type,
                organization.email ?? organization.phone ?? 'Sin contacto',
                <StatusBadge status={organization.status} feminine />,
                <StatusAction
                  status={organization.status}
                  pending={toggleStatus.isPending}
                  onDeactivate={() => {
                    if (window.confirm(`¿Inactivar la organización ${organization.name}? No se eliminará físicamente.`)) toggleStatus.mutate(organization);
                  }}
                  onActivate={() => {
                    if (window.confirm(`¿Activar ${organization.name} nuevamente?`)) toggleStatus.mutate(organization);
                  }}
                />,
              ])}
            />
          ) : null}
        </SectionCard>
      </div>
    </>
  );
}
