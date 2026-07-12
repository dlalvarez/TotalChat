import type { AvailabilityException, Appointment, PractitionerAvailabilityRule } from '../../api/adminResources';

export const APPOINTMENT_STATUS_OPTIONS = [
  { value: '', label: 'Todos' }, { value: 'scheduled', label: 'Programada' }, { value: 'cancelled', label: 'Cancelada' }, { value: 'completed', label: 'Atendida' }, { value: 'no_show', label: 'No asistió' },
];
export const toDateInput = (date: Date) => date.toISOString().slice(0, 10);
export const formatDateTime = (value: string) => value.slice(0, 16).replace('T', ' ');
export const formatTimeRange = (startsAt: string, endsAt: string) => `${startsAt.slice(11, 16)} - ${endsAt.slice(11, 16)}`;
export type AgendaItem = { id: string; kind: 'available' | 'appointment' | 'block'; starts_at: string; ends_at: string; appointment?: Appointment; block?: AvailabilityException };
const minutes = (time: string) => { const [h, m] = time.slice(0, 5).split(':').map(Number); return h * 60 + m; };
const isoAt = (date: string, total: number) => `${date}T${String(Math.floor(total / 60)).padStart(2, '0')}:${String(total % 60).padStart(2, '0')}:00`;
const operationalDateTime = (value: string) => value.slice(0, 19);
export const belongsToSelectedDate = (startsAt: string, selectedDate: string) => operationalDateTime(startsAt).slice(0, 10) === selectedDate;
export const overlapsHalfOpenRange = (eventStart: string, eventEnd: string, slotStart: string, slotEnd: string) => operationalDateTime(eventStart) < operationalDateTime(slotEnd) && operationalDateTime(eventEnd) > operationalDateTime(slotStart);
const dayOfWeekForDate = (date: string) => { const [year, month, day] = date.split('-').map(Number); const jsDay = new Date(year, month - 1, day).getDay(); return jsDay === 0 ? 6 : jsDay - 1; };
export function activeAgendaAvailabilityRules({ selectedDate, practitionerId, serviceId, rules }: { selectedDate: string; practitionerId: string; serviceId?: string; rules: PractitionerAvailabilityRule[] }) {
  const dayOfWeek = dayOfWeekForDate(selectedDate);
  return rules.filter((r) => r.status === 'active' && r.practitioner_id === practitionerId && r.day_of_week === dayOfWeek && (!serviceId || !r.practitioner_service_id || r.practitioner_service_id === serviceId) && r.valid_from <= selectedDate && (!r.valid_to || r.valid_to >= selectedDate));
}
export function buildAgendaItems({ selectedDate, practitionerId, serviceId, slotMinutes, rules, appointments, blocks }: { selectedDate: string; practitionerId: string; serviceId?: string; slotMinutes: number; rules: PractitionerAvailabilityRule[]; appointments: Appointment[]; blocks: AvailabilityException[] }): AgendaItem[] {
  const activeRules = activeAgendaAvailabilityRules({ selectedDate, practitionerId, serviceId, rules });
  if (activeRules.length === 0) return [];
  const scheduledAppointments = appointments.filter((a) => a.status === 'scheduled' && a.practitioner_id === practitionerId && belongsToSelectedDate(a.starts_at, selectedDate));
  const activeBlocks = blocks.filter((b) => b.status === 'active' && b.practitioner_id === practitionerId && overlapsHalfOpenRange(b.starts_at, b.ends_at, `${selectedDate}T00:00:00`, `${selectedDate}T23:59:59`));

  const generated = new Map<string, AgendaItem>();
  activeRules.forEach((r) => {
    for (let start = minutes(r.start_time); start + slotMinutes <= minutes(r.end_time); start += slotMinutes) {
      const starts_at = isoAt(selectedDate, start); const ends_at = isoAt(selectedDate, start + slotMinutes); const id = `${starts_at}-${ends_at}`;
      if (generated.has(id)) continue;
      const appointment = scheduledAppointments.find((a) => overlapsHalfOpenRange(a.starts_at, a.ends_at, starts_at, ends_at));
      const block = activeBlocks.find((b) => overlapsHalfOpenRange(b.starts_at, b.ends_at, starts_at, ends_at));
      generated.set(id, { id, kind: appointment ? 'appointment' : block ? 'block' : 'available', starts_at, ends_at, appointment, block });
    }
  });

  const generatedItems = [...generated.values()];
  const extras: AgendaItem[] = [
    ...scheduledAppointments.filter((a) => !generatedItems.some((item) => item.appointment?.id === a.id)).map((appointment) => ({ id: `appointment-${appointment.id}`, kind: 'appointment' as const, starts_at: appointment.starts_at, ends_at: appointment.ends_at, appointment })),
    ...activeBlocks.filter((b) => !generatedItems.some((item) => item.block?.id === b.id)).map((block) => ({ id: `block-${block.id}`, kind: 'block' as const, starts_at: block.starts_at, ends_at: block.ends_at, block })),
  ];
  return [...generatedItems, ...extras].sort((a, b) => a.starts_at.localeCompare(b.starts_at));
}
export function appointmentErrorMessage(message: string) {
  if (message === 'Appointment overlaps an active availability exception.') return 'No se puede crear o reprogramar la cita porque el profesional tiene un bloqueo activo en ese horario.';
  if (message === 'Practitioner already has a scheduled appointment in this time range.') return 'No se puede crear o reprogramar la cita porque el profesional ya tiene una cita programada en ese horario.';
  if (message === 'Room already has a scheduled appointment in this time range.') return 'No se puede crear o reprogramar la cita porque el consultorio ya está ocupado en ese horario.';
  return message;
}
