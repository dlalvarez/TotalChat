import { Badge } from '../../components/ui/Badge';
import { EmptyState } from '../../components/ui/States';
import type { AvailabilityException, Appointment } from '../../api/adminResources';
import { buildAgendaEvents, formatTimeRange } from './appointmentUtils';
export function AppointmentDailyAgenda({ selectedDate, appointments, blocks }: { selectedDate: string; appointments: Appointment[]; blocks: AvailabilityException[] }) {
  const events = buildAgendaEvents(appointments, blocks);
  if (events.length === 0) return <EmptyState title="Día disponible" description={`No hay citas ni bloqueos activos para ${selectedDate}. La vista queda preparada para sumar slots visuales en una fase futura.`} />;
  return <div className="space-y-3">{events.map((e) => <article key={`${e.kind}-${e.id}`} className={`rounded-2xl border p-4 ${e.kind === 'block' ? 'border-amber-200 bg-amber-50' : 'border-brand-100 bg-white'}`}><div className="flex flex-wrap items-start justify-between gap-3"><div><p className="text-sm font-bold text-slate-950">{formatTimeRange(e.starts_at, e.ends_at)}</p><h3 className="mt-1 text-lg font-semibold">{e.title}</h3><p className="text-sm text-slate-600">{e.subtitle}</p><p className="text-xs text-slate-500">{e.meta}</p></div><Badge tone={e.kind === 'block' ? 'warning' : 'info'}>{e.kind === 'block' ? 'Bloqueado' : e.status ?? 'Ocupado por cita'}</Badge></div></article>)}</div>;
}
