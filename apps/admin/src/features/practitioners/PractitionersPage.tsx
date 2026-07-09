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
import { FieldWrapper, Input } from '../../components/ui/Form';
import { EmptyState, ErrorState, LoadingState } from '../../components/ui/States';
import { adminResourcesApi } from '../../api/adminResources';
import type { AdminTenant } from '../../config/tenant';

const schema = z.object({
  full_name: z.string().min(1, 'El nombre completo es obligatorio'),
  professional_type: z.string().optional(),
  professional_license: z.string().optional(),
  email: z.string().email('Ingresa un correo válido').or(z.literal('')).optional(),
  phone: z.string().optional(),
});

type FormValues = z.infer<typeof schema>;
const emptyToNull = (value?: string) => (value && value.trim().length > 0 ? value.trim() : null);

export function PractitionersPage({ tenant }: { tenant: AdminTenant }) {
  const [showForm, setShowForm] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const queryClient = useQueryClient();
  const practitionersKey = useMemo(() => ['practitioners', tenant.id], [tenant.id]);

  const practitioners = useQuery({ queryKey: practitionersKey, queryFn: () => adminResourcesApi.listPractitioners(tenant.id) });
  const form = useForm<FormValues>({ resolver: zodResolver(schema) });

  const create = useMutation({
    mutationFn: (values: FormValues) =>
      adminResourcesApi.createPractitioner(tenant.id, {
        full_name: values.full_name.trim(),
        professional_type: emptyToNull(values.professional_type),
        professional_license: emptyToNull(values.professional_license),
        email: emptyToNull(values.email),
        phone: emptyToNull(values.phone),
      }),
    onSuccess: async () => {
      setFeedback('Profesional creado correctamente.');
      form.reset();
      setShowForm(false);
      await queryClient.invalidateQueries({ queryKey: practitionersKey });
    },
  });

  return (
    <>
      <PageHeader
        eyebrow="Fase 6B.2 · módulo funcional"
        title="Profesionales"
        description="Gestiona profesionales con campos legibles. Especialidades y servicios permanecen diferidos para fases posteriores."
        actions={<Button onClick={() => setShowForm((value) => !value)}>{showForm ? 'Cerrar formulario' : 'Crear profesional'}</Button>}
      />

      {feedback ? <div className="mb-4 rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-sm font-medium text-emerald-800">{feedback}</div> : null}
      {create.isError ? <div className="mb-4"><ErrorState description={(create.error as Error).message} /></div> : null}

      {showForm ? (
        <SectionCard title="Nuevo profesional" description="Registra datos básicos. La asignación de especialidades y servicios no pertenece a esta fase.">
          <form className="grid gap-4 md:grid-cols-2" onSubmit={form.handleSubmit((values) => create.mutate(values))}>
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
            <div className="md:col-span-2"><Button type="submit" disabled={create.isPending}>{create.isPending ? 'Creando…' : 'Guardar profesional'}</Button></div>
          </form>
        </SectionCard>
      ) : null}

      <div className="mt-6">
        <SectionCard title="Listado de profesionales" description={`Tenant activo: ${tenant.label}`}>
          {practitioners.isLoading ? <LoadingState label="Cargando profesionales…" /> : null}
          {practitioners.isError ? <ErrorState description={(practitioners.error as Error).message} /> : null}
          {practitioners.isSuccess && practitioners.data.length === 0 ? <EmptyState title="Sin profesionales" description="Crea el primer profesional con datos básicos. Especialidades y servicios vendrán después." /> : null}
          {practitioners.isSuccess && practitioners.data.length > 0 ? (
            <DataTableShell columns={['Profesional', 'Tipo', 'Registro', 'Contacto', 'Estado']} rows={practitioners.data.map((practitioner) => [<strong>{practitioner.full_name}</strong>, practitioner.professional_type ?? 'Sin tipo', practitioner.professional_license ?? 'Sin registro', practitioner.email ?? practitioner.phone ?? 'Sin contacto', <Badge tone={practitioner.status === 'active' ? 'success' : 'neutral'}>{practitioner.status === 'active' ? 'Activo' : 'Inactivo'}</Badge>])} />
          ) : null}
        </SectionCard>
      </div>
    </>
  );
}
