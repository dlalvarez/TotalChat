import { useMemo, useRef, useState } from 'react';
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
import {
  adminResourcesApi,
  type Practitioner,
  type PractitionerSpecialty,
  type Specialty,
} from '../../api/adminResources';
import type { AdminTenant } from '../../config/tenant';
import { NameEditButton, StatusAction, StatusBadge } from '../adminResourceUtils';
import { emptyToNull } from '../adminResourceFormat';

const schema = z.object({
  full_name: z.string().min(1, 'El nombre completo es obligatorio'),
  professional_type: z.string().optional(),
  professional_license: z.string().optional(),
  email: z.string().email('Ingresa un correo válido').or(z.literal('')).optional(),
  phone: z.string().optional(),
});

type FormValues = z.infer<typeof schema>;

const defaults = (practitioner?: Practitioner): FormValues => ({
  full_name: practitioner?.full_name ?? '',
  professional_type: practitioner?.professional_type ?? '',
  professional_license: practitioner?.professional_license ?? '',
  email: practitioner?.email ?? '',
  phone: practitioner?.phone ?? '',
});

function Chip({ label, inactive, onRemove }: { label: string; inactive?: boolean; onRemove: () => void }) {
  return (
    <span className="inline-flex items-center gap-2 rounded-full border border-brand-100 bg-brand-50 px-3 py-1 text-sm font-medium text-brand-800">
      {label}
      {inactive ? <span className="text-xs text-amber-700">inactiva</span> : null}
      <button type="button" className="text-brand-700 hover:text-brand-950" onClick={onRemove}>
        ×
      </button>
    </span>
  );
}

export function PractitionersPage({ tenant }: { tenant: AdminTenant }) {
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<Practitioner | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [selected, setSelected] = useState<PractitionerSpecialty[]>([]);
  const [search, setSearch] = useState('');
  const [loadingAssignments, setLoadingAssignments] = useState(false);
  const assignmentRequestRef = useRef(0);
  const queryClient = useQueryClient();
  const practitionersKey = useMemo(() => ['practitioners', tenant.id], [tenant.id]);
  const specialtiesKey = useMemo(() => ['specialties', tenant.id], [tenant.id]);

  const practitioners = useQuery({
    queryKey: practitionersKey,
    queryFn: () => adminResourcesApi.listPractitioners(tenant.id),
  });
  const specialties = useQuery({
    queryKey: specialtiesKey,
    queryFn: () => adminResourcesApi.listSpecialties(tenant.id),
  });
  const form = useForm<FormValues>({ resolver: zodResolver(schema), defaultValues: defaults() });

  const payload = (values: FormValues) => ({
    full_name: values.full_name.trim(),
    professional_type: emptyToNull(values.professional_type),
    professional_license: emptyToNull(values.professional_license),
    email: emptyToNull(values.email),
    phone: emptyToNull(values.phone),
  });

  const closeForm = () => {
    assignmentRequestRef.current += 1;
    setEditing(null);
    setShowForm(false);
    setSelected([]);
    setSearch('');
    setLoadingAssignments(false);
    setFormError(null);
    form.reset(defaults());
  };

  const save = useMutation({
    mutationFn: async (values: FormValues) => {
      setFormError(null);
      const specialtyIds = selected.map((specialty) => specialty.specialty_id);
      const saved = editing
        ? await adminResourcesApi.updatePractitioner(tenant.id, editing.id, payload(values))
        : await adminResourcesApi.createPractitioner(tenant.id, payload(values));

      try {
        await adminResourcesApi.syncPractitionerSpecialties(tenant.id, saved.id, specialtyIds);
      } catch (error) {
        if (!editing) {
          setEditing(saved);
          setShowForm(true);
        }
        throw new Error(
          editing
            ? (error as Error).message
            : `El profesional fue creado, pero no se pudieron sincronizar sus especialidades. Reabre o guarda nuevamente el profesional. ${(error as Error).message}`,
        );
      }
      return saved;
    },
    onSuccess: async () => {
      setFeedback(editing ? 'Profesional actualizado correctamente.' : 'Profesional creado correctamente.');
      closeForm();
      await queryClient.invalidateQueries({ queryKey: practitionersKey });
    },
    onError: async (error) => {
      setFormError((error as Error).message);
      await queryClient.invalidateQueries({ queryKey: practitionersKey });
    },
  });

  const statusAction = useMutation({
    mutationFn: (practitioner: Practitioner) =>
      practitioner.status === 'active'
        ? adminResourcesApi.disablePractitioner(tenant.id, practitioner.id)
        : adminResourcesApi.activatePractitioner(tenant.id, practitioner.id),
    onSuccess: async (_updated, practitioner) => {
      setFeedback(
        practitioner.status === 'active'
          ? 'Profesional inactivado correctamente.'
          : 'Profesional activado correctamente.',
      );
      await queryClient.invalidateQueries({ queryKey: practitionersKey });
    },
  });

  const startEdit = async (practitioner: Practitioner) => {
    const requestId = assignmentRequestRef.current + 1;
    assignmentRequestRef.current = requestId;
    setEditing(practitioner);
    form.reset(defaults(practitioner));
    setShowForm(true);
    setSelected([]);
    setSearch('');
    setFormError(null);
    setLoadingAssignments(true);

    try {
      const assignments = await adminResourcesApi.listPractitionerSpecialties(tenant.id, practitioner.id);
      if (assignmentRequestRef.current === requestId) {
        setSelected(assignments.filter((assignment) => assignment.status === 'active'));
      }
    } catch (error) {
      if (assignmentRequestRef.current === requestId) {
        setFormError((error as Error).message || 'No se pudieron cargar las especialidades del profesional.');
      }
    } finally {
      if (assignmentRequestRef.current === requestId) {
        setLoadingAssignments(false);
      }
    }
  };

  const selectable = (specialties.data ?? []).filter(
    (specialty: Specialty) =>
      specialty.status === 'active' &&
      !selected.some((assignment) => assignment.specialty_id === specialty.id) &&
      specialty.name.toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <>
      <PageHeader
        eyebrow="Fase 6B.4 · especialidades múltiples"
        title="Profesionales"
        description="Gestiona profesionales y sus especialidades mediante nombres legibles."
        actions={
          <Button onClick={() => (showForm ? closeForm() : setShowForm(true))}>
            {showForm ? 'Cerrar formulario' : 'Crear profesional'}
          </Button>
        }
      />

      {feedback ? (
        <div className="mb-4 rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-sm font-medium text-emerald-800">
          {feedback}
        </div>
      ) : null}
      {formError ? <div className="mb-4"><ErrorState description={formError} /></div> : null}
      {statusAction.isError ? <div className="mb-4"><ErrorState description={(statusAction.error as Error).message} /></div> : null}

      {showForm ? (
        <SectionCard
          title={editing ? `Editar ${editing.full_name}` : 'Nuevo profesional'}
          description="Registra datos básicos y asigna cero, una o múltiples especialidades."
        >
          <form className="grid gap-4 md:grid-cols-2" onSubmit={form.handleSubmit((values) => save.mutate(values))}>
            <FieldWrapper label="Nombre completo" error={form.formState.errors.full_name?.message}>
              <Input placeholder="Dra. Ana Pérez" {...form.register('full_name')} />
            </FieldWrapper>
            <FieldWrapper label="Tipo profesional" error={form.formState.errors.professional_type?.message}>
              <Input placeholder="Médico general" {...form.register('professional_type')} />
            </FieldWrapper>
            <FieldWrapper label="Registro / licencia profesional" error={form.formState.errors.professional_license?.message}>
              <Input placeholder="RM 123456" {...form.register('professional_license')} />
            </FieldWrapper>
            <FieldWrapper label="Correo" error={form.formState.errors.email?.message}>
              <Input type="email" placeholder="profesional@clinica.com" {...form.register('email')} />
            </FieldWrapper>
            <FieldWrapper label="Teléfono" error={form.formState.errors.phone?.message}>
              <Input placeholder="+57 300 000 0000" {...form.register('phone')} />
            </FieldWrapper>
            <FieldWrapper
              label="Especialidades"
              hint={
                loadingAssignments
                  ? 'Cargando especialidades asignadas…'
                  : specialties.isLoading
                    ? 'Cargando catálogo de especialidades…'
                    : specialties.isError
                      ? 'No se pudieron cargar las especialidades.'
                      : specialties.data?.length === 0
                        ? 'No existen especialidades. Créalas en el módulo Especialidades.'
                        : 'Busca y selecciona varias especialidades.'
              }
            >
              <div className="space-y-2">
                {loadingAssignments ? <LoadingState label="Cargando especialidades del profesional…" /> : null}
                <Input
                  placeholder="Buscar por nombre"
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  disabled={loadingAssignments || specialties.isLoading || specialties.isError}
                />
                <div className="flex flex-wrap gap-2">
                  {selected.map((assignment) => (
                    <Chip
                      key={assignment.specialty_id}
                      label={assignment.specialty_name ?? 'Especialidad'}
                      inactive={assignment.specialty_status === 'inactive'}
                      onRemove={() =>
                        setSelected(selected.filter((item) => item.specialty_id !== assignment.specialty_id))
                      }
                    />
                  ))}
                </div>
                {search && selectable.length > 0 ? (
                  <div className="rounded-xl border border-slate-200 bg-white p-2 shadow-sm">
                    {selectable.slice(0, 6).map((specialty) => (
                      <button
                        key={specialty.id}
                        type="button"
                        className="block w-full rounded-lg px-3 py-2 text-left text-sm hover:bg-slate-50"
                        onClick={() => {
                          setSelected([
                            ...selected,
                            {
                              practitioner_id: editing?.id ?? '',
                              specialty_id: specialty.id,
                              specialty_name: specialty.name,
                              specialty_status: specialty.status,
                              status: 'active',
                            },
                          ]);
                          setSearch('');
                        }}
                      >
                        {specialty.name}
                      </button>
                    ))}
                  </div>
                ) : null}
              </div>
            </FieldWrapper>
            <div className="flex gap-2 md:col-span-2">
              <Button type="submit" disabled={save.isPending || loadingAssignments}>
                {save.isPending ? 'Guardando…' : 'Guardar cambios'}
              </Button>
              {editing ? <Button type="button" variant="secondary" onClick={closeForm}>Cancelar</Button> : null}
            </div>
          </form>
        </SectionCard>
      ) : null}

      <div className="mt-6">
        <SectionCard title="Listado de profesionales" description={`Tenant activo: ${tenant.label}`}>
          {practitioners.isLoading ? <LoadingState label="Cargando profesionales…" /> : null}
          {practitioners.isError ? <ErrorState description={(practitioners.error as Error).message} /> : null}
          {practitioners.isSuccess && practitioners.data.length === 0 ? (
            <EmptyState title="Sin profesionales" description="Crea el primer profesional con datos básicos." />
          ) : null}
          {practitioners.isSuccess && practitioners.data.length > 0 ? (
            <DataTableShell
              columns={['Profesional', 'Tipo', 'Registro', 'Contacto', 'Estado', 'Acciones']}
              rows={practitioners.data.map((practitioner) => [
                <NameEditButton name={practitioner.full_name} onEdit={() => void startEdit(practitioner)} />,
                practitioner.professional_type ?? 'Sin tipo',
                practitioner.professional_license ?? 'Sin registro',
                practitioner.email ?? practitioner.phone ?? 'Sin contacto',
                <StatusBadge status={practitioner.status} />,
                <StatusAction
                  status={practitioner.status}
                  entityName={practitioner.full_name}
                  disabled={statusAction.isPending}
                  onInactivate={() => statusAction.mutate(practitioner)}
                  onActivate={() => statusAction.mutate(practitioner)}
                />,
              ])}
            />
          ) : null}
        </SectionCard>
      </div>
    </>
  );
}
