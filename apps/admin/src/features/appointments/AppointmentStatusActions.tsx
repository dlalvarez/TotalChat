import { Button } from '../../components/ui/Button';
import type { Appointment } from '../../api/adminResources';
export function AppointmentStatusActions({ appointment, disabled, onCancel, onComplete, onNoShow }: { appointment: Appointment; disabled?: boolean; onCancel: () => void; onComplete: () => void; onNoShow: () => void }) {
  if (appointment.status !== 'scheduled') return <span className="text-xs text-slate-500">Ver</span>;
  return <div className="flex flex-wrap gap-2"><Button variant="secondary" disabled={disabled} onClick={onCancel}>Cancelar</Button><Button variant="secondary" disabled={disabled} onClick={onComplete}>Marcar atendida</Button><Button variant="secondary" disabled={disabled} onClick={onNoShow}>No asistió</Button></div>;
}
