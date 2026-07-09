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
  location_id: z.string().min(1, 'Selecciona una sede'),
  name: z.string().min(1, 'El nombre del consultorio es obligatorio'),
  room_type: z.string().optional(),
  capacity: z.preprocess(
    (value) => (value === '' || value === undefined || value === null ? undefined : Number(value)),
    z.number({ invalid_type_error: 'La capacidad debe ser un número' }).int('La capacidad debe ser un número entero').positive('La capacidad debe ser positiva').optional(),
  ),
});

type FormValues = z.infer<typeof schema>;
const emptyToNull = (value?: string) => (value && value.trim().length > 0 ? value.trim() : null);

export function RoomsPage({ tenant }: { tenant: AdminTenant }) {
  const [showForm, setShowForm] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const queryClient = useQueryClient();
  const roomsKey = useMemo(() => ['rooms', tenant.id], [tenant.id]);
  const locationsKey = useMemo(() => ['locations', tenant.id], [tenant.id]);

  const rooms = useQuery({ queryKey: roomsKey, queryFn: () => adminResourcesApi.listRooms(tenant.id) });
  const locations = useQuery({ queryKey: locationsKey, queryFn: () => adminResourcesApi.listLocations(tenant.id) });
  const locationNames = new Map((locations.data ?? []).map((location) => [location.id, location.name]));

  const form = useForm<FormValues>({ resolver: zodResolver(schema) });

  const create = useMutation({
    mutationFn: (values: FormValues) =>
      adminResourcesApi.createRoom(tenant.id, {
        location_id: values.location_id,
        name: values.name.trim(),
        room_type: emptyToNull(values.room_type),
        capacity: values.capacity ?? null,
      }),
    onSuccess: async () => {
      setFeedback('Consultorio creado correctamente.');
      form.reset();
      setShowForm(false);
      await queryClient.invalidateQueries({ queryKey: roomsKey });
    },
  });

  return (
    <>
      <PageHeader
        eyebrow="Fase 6B.2 · módulo funcional"
        title="Consultorios"
        description="Gestiona consultorios asociados a sedes. La sede se selecciona por nombre y su UUID permanece interno."
        actions={<Button onClick={() => setShowForm((value) => !value)}>{showForm ? 'Cerrar formulario' : 'Crear consultorio'}</Button>}
      />

      {feedback ? <div className="mb-4 rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-sm font-medium text-emerald-800">{feedback}</div> : null}
      {create.isError ? <div className="mb-4"><ErrorState description={(create.error as Error).message} /></div> : null}

      {showForm ? (
        <SectionCard title="Nuevo consultorio" description="Selecciona una sede existente por nombre y registra los datos operativos del consultorio.">
          <form className="grid gap-4 md:grid-cols-2" onSubmit={form.handleSubmit((values) => create.mutate(values))}>
            <FieldWrapper label="Sede" hint="Selector amigable; el identificador técnico queda interno." error={form.formState.errors.location_id?.message}>
              <Select {...form.register('location_id')} disabled={locations.isLoading || (locations.data?.length ?? 0) === 0}>
                <option value="">Selecciona una sede</option>
                {(locations.data ?? []).map((location) => <option key={location.id} value={location.id}>{location.name}</option>)}
              </Select>
            </FieldWrapper>
            <FieldWrapper label="Nombre del consultorio" error={form.formState.errors.name?.message}>
              <Input placeholder="Consultorio 201" {...form.register('name')} />
            </FieldWrapper>
            <FieldWrapper label="Tipo de consultorio" error={form.formState.errors.room_type?.message}>
              <Input placeholder="Consulta general" {...form.register('room_type')} />
            </FieldWrapper>
            <FieldWrapper label="Capacidad" error={form.formState.errors.capacity?.message}>
              <Input type="number" min="1" placeholder="1" {...form.register('capacity')} />
            </FieldWrapper>
            <div className="md:col-span-2"><Button type="submit" disabled={create.isPending || (locations.data?.length ?? 0) === 0}>{create.isPending ? 'Creando…' : 'Guardar consultorio'}</Button></div>
          </form>
        </SectionCard>
      ) : null}

      <div className="mt-6">
        <SectionCard title="Listado de consultorios" description={`Tenant activo: ${tenant.label}`}>
          {rooms.isLoading ? <LoadingState label="Cargando consultorios…" /> : null}
          {rooms.isError ? <ErrorState description={(rooms.error as Error).message} /> : null}
          {rooms.isSuccess && rooms.data.length === 0 ? <EmptyState title="Sin consultorios" description="Crea el primer consultorio usando una sede existente." /> : null}
          {rooms.isSuccess && rooms.data.length > 0 ? (
            <DataTableShell columns={['Consultorio', 'Sede', 'Tipo', 'Capacidad', 'Estado']} rows={rooms.data.map((room) => [<strong>{room.name}</strong>, locationNames.get(room.location_id) ?? 'Sede no disponible', room.room_type ?? 'Sin tipo', room.capacity ?? 'Sin capacidad', <Badge tone={room.status === 'active' ? 'success' : 'neutral'}>{room.status === 'active' ? 'Activo' : 'Inactivo'}</Badge>])} />
          ) : null}
        </SectionCard>
      </div>
    </>
  );
}
