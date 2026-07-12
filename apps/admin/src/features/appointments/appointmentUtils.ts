import type { AvailabilityException, Appointment } from '../../api/adminResources';

export const APPOINTMENT_STATUS_OPTIONS = [
  { value: '', label: 'Todos' }, { value: 'scheduled', label: 'Programada' }, { value: 'cancelled', label: 'Cancelada' }, { value: 'completed', label: 'Atendida' }, { value: 'no_show', label: 'No asistió' },
];
export const toDateInput = (date: Date) => date.toISOString().slice(0, 10);
export const formatDateTime = (value: string) => value.slice(0, 16).replace('T', ' ');
export const formatTimeRange = (startsAt: string, endsAt: string) => `${startsAt.slice(11, 16)} - ${endsAt.slice(11, 16)}`;
export type AgendaEvent = { id: string; kind: 'appointment' | 'block'; starts_at: string; ends_at: string; title: string; subtitle: string; meta: string; status?: string; source: Appointment | AvailabilityException };
export function buildAgendaEvents(appointments: Appointment[], blocks: AvailabilityException[]): AgendaEvent[] {
  return [
    ...appointments.map((a): AgendaEvent => ({ id: a.id, kind: 'appointment', starts_at: a.starts_at, ends_at: a.ends_at, title: a.patient_name ?? 'Paciente', subtitle: a.practitioner_service_name ?? 'Servicio', meta: [a.practitioner_name, a.location_name, a.room_name].filter(Boolean).join(' · '), status: a.status_label, source: a })),
    ...blocks.filter((b) => b.status === 'active').map((b): AgendaEvent => ({ id: b.id, kind: 'block', starts_at: b.starts_at, ends_at: b.ends_at, title: 'Bloqueado', subtitle: b.reason || b.exception_type_label, meta: [b.practitioner_name, b.location_name, b.room_name].filter(Boolean).join(' · ') || 'General', source: b })),
  ].sort((a, b) => a.starts_at.localeCompare(b.starts_at));
}
export function appointmentErrorMessage(message: string) {
  if (message === 'Appointment overlaps an active availability exception.') return 'No se puede crear la cita porque el profesional tiene un bloqueo activo en ese horario.';
  if (message === 'Practitioner already has a scheduled appointment in this time range.') return 'No se puede crear la cita porque el profesional ya tiene una cita programada en ese horario.';
  if (message === 'Room already has a scheduled appointment in this time range.') return 'No se puede crear la cita porque el consultorio ya está ocupado en ese horario.';
  return message;
}
