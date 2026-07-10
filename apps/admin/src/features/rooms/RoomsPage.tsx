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
import { adminResourcesApi, type Room } from '../../api/adminResources';
import type { AdminTenant } from '../../config/tenant';
import { emptyToNull } from '../adminResourceFormat';
import { NameEditButton, StatusAction, StatusBadge } from '../adminResourceUtils';

const capacitySchema = z.preprocess(
  (value) => (value === '' || value === undefined || value === null ? undefined : Number(value)),
  z.number({ invalid_type_error: 'La capacidad debe ser un número. Si no aplica, deja el campo vacío.' }).int('La capacidad debe ser un número entero').positive('La capacidad debe ser positiva').optional(),
);

const schema = z.object({
  location_id: z.string().min(1, 'Selecciona una sede'),
  name: z.string().min(1, 'El nombre del consultorio es obligatorio'),
  room_type: z.string().optional(),
  capacity: capacitySchema,
});

type FormValues = z.infer<typeof schema>;

function formDefaults(room?: Room): FormValues {
  return {
    location_id: room?.location_id ?? '',
    name: room?.name ?? '',
    room_type: room?.room_type ?? '',
    capacity: room?.capacity ?? undefined,
  };
}

function toPayload(values: FormValues) {
  return {
    location_id: values.location_id,
    name: values.name.trim(),
    room_type: emptyToNull(values.room_type),
    capacity: values.capacity ?? null,
  };
}

export function RoomsPage({ tenant }: { tenant: AdminTenant }) {
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<Room | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const queryClient = useQueryClient();
  const roomsKey = useMemo(() => ['rooms', tenant.id], [tenant.id]);
  const locationsKey = useMemo(() => ['locations', tenant.id], [tenant.id]);

  const rooms = useQuery({ queryKey: roomsKey, queryFn: () => adminResourcesApi.listRooms(tenant.id) });
  const locations = useQuery({ queryKey: locationsKey, queryFn: () => adminResourcesApi.listLocations(tenant.id) });
  const locationNames = new Map((locations.data ?? []).map((location) => [location.id, location.name]));
  const form = useForm<FormValues>({ resolver: zodResolver(schema), defaultValues: formDefaults() });

  const closeForm = () => {
    setEditing(null);
    setShowForm(false);
    form.reset(formDefaults());
  };

  const save = useMutation({
    mutationFn: (values: FormValues) =>
      editing
        ? adminResourcesApi.updateRoom(tenant.id, editing.id, toPayload(values))
        : adminResourcesApi.createRoom(tenant.id, toPayload(values)),
    onSuccess: async () => {
      setFeedback(editing ? 'Consultorio actualizado correctamente.' : 'Consultorio creado correctamente.');
      closeForm();
      await queryClient.invalidateQueries({ queryKey: roomsKey });
    },
  });

  const toggleStatus = useMutation({
    mutationFn: (room: Room) =>
      room.status === 'active'
        ? adminResourcesApi.disableRoom(tenant.id, room.id)
        : adminResourcesApi.activateRoom(tenant.id, room.id),
    onSuccess: async (room) => {
      setFeedback(room.status === 'active' ? 'Consultorio activado correctamente.' : 'Consultorio inactivado correctamente.');
      await queryClient.invalidateQueries({ queryKey: roomsKey });
    },
  });

  const startEdit = (room: Room) => {
    setEditing(room);
    form.reset(formDefaults(room));
    setShowForm(true);
  };

  return (
    <>
      <PageHeader
        eyebrow="Fase 6B.3 · edición e inactivación"
        title="Consultorios"
        description="Gestiona consultorios asociados a sedes mediante selectores legibles."
        actions={<Button onClick={() => (showForm ? closeForm() : setShowForm(true))}>{showForm ? 'Cerrar formulario' : 'Crear consultorio'}</Button>}
      />

      {feedback ? <div className="mb-4 rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-sm font-medium text-emerald-800">{feedback}</div> : null}
      {save.isError ? <div className="mb-4"><ErrorState description={(save.error as Error).message} /></div> : null}
      {toggleStatus.isError ? <div className="mb-4"><ErrorState description={(toggleStatus.error as Error).message} /></div> : null}

      {showForm ? (
        <SectionCard title={editing ? `Editar ${editing.name}` : 'Nuevo consultorio'} description="Selecciona una sede existente por nombre y registra datos operativos del consultorio.">
          <form className="grid gap-4 md:grid-cols-2" onSubmit={form.handleSubmit((values) => save.mutate(values))}>
            <FieldWrapper label="Sede" hint="Selector amigable; el identificador técnico queda interno." error={form.formState.errors.location_id?.message}>
              <Select {...form.register('location_id')} disabled={locations.isLoading || (locations.data?.length ?? 0) === 0}>
                <option value="">Selecciona una sede</option>
                {(locations.data ?? []).map((location) => <option key={location.id} value={location.id}>{location.name}</option>)}
              </Select>
            </FieldWrapper>
            <FieldWrapper label="Nombre del consultorio" error={form.formState.errors.name?.message}><Input placeholder="Consultorio 201" {...form.register('name')} /></FieldWrapper>
            <FieldWrapper label="Tipo de consultorio" hint="Ejemplos: Consulta general, Procedimientos, Terapia, Diagnóstico, Virtual, Otro." error={form.formState.errors.room_type?.message}><Input placeholder="Consulta general" {...form.register('room_type')} /></FieldWrapper>
            <FieldWrapper label="Capacidad" hint="Para un consultorio individual normalmente usa 1. Si no aplica, déjalo vacío." error={form.formState.errors.capacity?.message}><Input type="number" min="1" placeholder="1" {...form.register('capacity')} /></FieldWrapper>
            <div className="flex gap-2 md:col-span-2">
              <Button type="submit" disabled={save.isPending || (locations.data?.length ?? 0) === 0}>{save.isPending ? 'Guardando…' : 'Guardar cambios'}</Button>
              {editing ? <Button type="button" variant="secondary" onClick={closeForm}>Cancelar</Button> : null}
            </div>
          </form>
        </SectionCard>
      ) : null}

      <div className="mt-6">
        <SectionCard title="Listado de consultorios" description={`Tenant activo: ${tenant.label}`}>
          {rooms.isLoading ? <LoadingState label="Cargando consultorios…" /> : null}
          {rooms.isError ? <ErrorState description={(rooms.error as Error).message} /> : null}
          {rooms.isSuccess && rooms.data.length === 0 ? <EmptyState title="Sin consultorios" description="Crea el primer consultorio usando una sede existente." /> : null}
          {rooms.isSuccess && rooms.data.length > 0 ? (
            <DataTableShell
              columns={['Consultorio', 'Sede', 'Tipo', 'Capacidad', 'Estado', 'Acciones']}
              rows={rooms.data.map((room) => [
                <NameEditButton onClick={() => startEdit(room)}>{room.name}</NameEditButton>,
                locationNames.get(room.location_id) ?? 'Sede no disponible',
                room.room_type ?? 'Sin tipo',
                room.capacity ?? 'Sin capacidad',
                <StatusBadge status={room.status} />,
                <StatusAction
                  status={room.status}
                  pending={toggleStatus.isPending}
                  onDeactivate={() => {
                    if (window.confirm(`¿Inactivar el consultorio ${room.name}? No se eliminará físicamente.`)) toggleStatus.mutate(room);
                  }}
                  onActivate={() => {
                    if (window.confirm(`¿Activar ${room.name} nuevamente?`)) toggleStatus.mutate(room);
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
