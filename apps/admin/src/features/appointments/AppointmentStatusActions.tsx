import { Button } from '../../components/ui/Button';
import type { Appointment } from '../../api/adminResources';

const isFinished = (appointment: Appointment) => new Date(appointment.ends_at).getTime() <= Date.now();

export function AppointmentStatusActions({ appointment, disabled, onEdit, onCancel, onComplete, onNoShow }: { appointment: Appointment; disabled?: boolean; onEdit: () => void; onCancel: () => void; onComplete: () => void; onNoShow: () => void }) {
  if (appointment.status !== 'scheduled') return <Button variant="secondary" disabled={disabled} onClick={onEdit}>Ver / Editar notas</Button>;
  const finished = isFinished(appointment);
  return <div className="flex flex-wrap gap-2"><Button variant="secondary" disabled={disabled} onClick={onEdit}>{finished ? 'Editar notas' : 'Editar / Reprogramar'}</Button><Button variant="secondary" disabled={disabled} onClick={onCancel}>Cancelar</Button>{finished ? <><Button variant="secondary" disabled={disabled} onClick={onComplete}>Marcar atendida</Button><Button variant="secondary" disabled={disabled} onClick={onNoShow}>No asistió</Button></> : null}</div>;
}
