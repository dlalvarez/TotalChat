import { DataTableShell } from '../../components/ui/DataTable';
import type { Appointment } from '../../api/adminResources';
import { formatDateTime } from './appointmentUtils';
import { AppointmentStatusActions } from './AppointmentStatusActions';
export function AppointmentList({ appointments, actionPending, onCancel, onComplete, onNoShow }: { appointments: Appointment[]; actionPending?: boolean; onCancel: (a: Appointment) => void; onComplete: (a: Appointment) => void; onNoShow: (a: Appointment) => void }) {
  return <DataTableShell columns={['Paciente', 'Profesional', 'Servicio', 'Sede', 'Consultorio', 'Fecha/hora', 'Estado', 'Acciones']} rows={appointments.map((a) => [a.patient_name ?? 'Paciente', a.practitioner_name ?? 'Profesional', a.practitioner_service_name ?? 'Servicio', a.location_name ?? 'Sede', a.room_name ?? '—', `${formatDateTime(a.starts_at)} → ${formatDateTime(a.ends_at)}`, a.status_label, <AppointmentStatusActions appointment={a} disabled={actionPending} onCancel={() => onCancel(a)} onComplete={() => onComplete(a)} onNoShow={() => onNoShow(a)} />])} />;
}
