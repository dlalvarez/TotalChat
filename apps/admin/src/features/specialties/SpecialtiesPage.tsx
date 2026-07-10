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
import { adminResourcesApi, type Specialty } from '../../api/adminResources';
import type { AdminTenant } from '../../config/tenant';
import { NameEditButton, StatusAction, StatusBadge } from '../adminResourceUtils';
import { emptyToNull } from '../adminResourceFormat';

const schema = z.object({
  name: z.string().min(1, 'El nombre de la especialidad es obligatorio'),
  description: z.string().optional(),
});

type FormValues = z.infer<typeof schema>;

const defaults = (specialty?: Specialty): FormValues => ({
  name: specialty?.name ?? '',
  description: specialty?.description ?? '',
});

export function SpecialtiesPage({ tenant }: { tenant: AdminTenant }) {
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<Specialty | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const queryClient = useQueryClient();
  const specialtiesKey = useMemo(() => ['specialties', tenant.id], [tenant.id]);

  const specialties = useQuery({
    queryKey: specialtiesKey,
    queryFn: () => adminResourcesApi.listSpecialties(tenant.id),
  });
  const form = useForm<FormValues>({ resolver: zodResolver(schema), defaultValues: defaults() });

  const payload = (values: FormValues) => ({
    name: values.name.trim(),
    description: emptyToNull(values.description),
  });

  const closeForm = () => {
    setEditing(null);
    setShowForm(false);
    form.reset(defaults());
  };

  const save = useMutation({
    mutationFn: (values: FormValues) =>
      editing
        ? adminResourcesApi.updateSpecialty(tenant.id, editing.id, payload(values))
        : adminResourcesApi.createSpecialty(tenant.id, payload(values)),
    onSuccess: async () => {
      setFeedback(editing ? 'Especialidad actualizada correctamente.' : 'Especialidad creada correctamente.');
      closeForm();
      await queryClient.invalidateQueries({ queryKey: specialtiesKey });
    },
  });

  const statusAction = useMutation({
    mutationFn: (specialty: Specialty) =>
      specialty.status === 'active'
        ? adminResourcesApi.disableSpecialty(tenant.id, specialty.id)
        : adminResourcesApi.activateSpecialty(tenant.id, specialty.id),
    onSuccess: async (_updated, specialty) => {
      setFeedback(
        specialty.status === 'active'
          ? 'Especialidad inactivada correctamente.'
          : 'Especialidad activada correctamente.',
      );
      await queryClient.invalidateQueries({ queryKey: specialtiesKey });
    },
  });

  const startEdit = (specialty: Specialty) => {
    setEditing(specialty);
    form.reset(defaults(specialty));
    setShowForm(true);
  };

  return (
    <>
      <PageHeader
        eyebrow="Fase 6B.4 · especialidades"
        title="Especialidades"
        description="Administra el catálogo de especialidades del tenant sin borrar físicamente registros."
        actions={
          <Button onClick={() => (showForm ? closeForm() : setShowForm(true))}>
            {showForm ? 'Cerrar formulario' : 'Crear especialidad'}
          </Button>
        }
      />

      {feedback ? (
        <div className="mb-4 rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-sm font-medium text-emerald-800">
          {feedback}
        </div>
      ) : null}
      {save.isError ? <div className="mb-4"><ErrorState description={(save.error as Error).message} /></div> : null}
      {statusAction.isError ? (
        <div className="mb-4"><ErrorState description={(statusAction.error as Error).message} /></div>
      ) : null}

      {showForm ? (
        <SectionCard
          title={editing ? `Editar ${editing.name}` : 'Nueva especialidad'}
          description="Usa nombres legibles; el identificador técnico permanece interno."
        >
          <form className="grid gap-4 md:grid-cols-2" onSubmit={form.handleSubmit((values) => save.mutate(values))}>
            <FieldWrapper label="Nombre" error={form.formState.errors.name?.message}>
              <Input placeholder="Pediatría" {...form.register('name')} />
            </FieldWrapper>
            <FieldWrapper label="Descripción" error={form.formState.errors.description?.message}>
              <Input placeholder="Descripción administrativa opcional" {...form.register('description')} />
            </FieldWrapper>
            <div className="flex gap-2 md:col-span-2">
              <Button type="submit" disabled={save.isPending}>{save.isPending ? 'Guardando…' : 'Guardar cambios'}</Button>
              {editing ? <Button type="button" variant="secondary" onClick={closeForm}>Cancelar</Button> : null}
            </div>
          </form>
        </SectionCard>
      ) : null}

      <div className="mt-6">
        <SectionCard title="Listado de especialidades" description={`Tenant activo: ${tenant.label}`}>
          {specialties.isLoading ? <LoadingState label="Cargando especialidades…" /> : null}
          {specialties.isError ? <ErrorState description={(specialties.error as Error).message} /> : null}
          {specialties.isSuccess && specialties.data.length === 0 ? (
            <EmptyState
              title="Sin especialidades"
              description="Crea Pediatría, Nefrología u otras especialidades propias del tenant."
            />
          ) : null}
          {specialties.isSuccess && specialties.data.length > 0 ? (
            <DataTableShell
              columns={['Especialidad', 'Descripción', 'Estado', 'Acciones']}
              rows={specialties.data.map((specialty) => [
                <NameEditButton name={specialty.name} onEdit={() => startEdit(specialty)} />,
                specialty.description ?? 'Sin descripción',
                <StatusBadge status={specialty.status} />,
                <StatusAction
                  status={specialty.status}
                  entityName={specialty.name}
                  disabled={statusAction.isPending}
                  onInactivate={() => statusAction.mutate(specialty)}
                  onActivate={() => statusAction.mutate(specialty)}
                />,
              ])}
            />
          ) : null}
        </SectionCard>
      </div>
    </>
  );
}
