import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { DataTableShell } from '../../components/ui/DataTable';
import type { Patient } from '../../api/adminResources';
import { NameEditButton } from '../adminResourceUtils';
import { patientDocument, patientStatusLabel, patientStatusTone } from './patientUtils';

export function PatientList({ patients, actionPending, onEdit, onDisable, onReactivate }: { patients: Patient[]; actionPending?: boolean; onEdit: (patient: Patient) => void; onDisable: (patient: Patient) => void; onReactivate: (patient: Patient) => void }) {
  return (
    <DataTableShell
      columns={['Paciente', 'Documento', 'Teléfono', 'Email', 'Estado', 'Acciones']}
      rows={patients.map((patient) => [
        <NameEditButton name={patient.full_name} onEdit={() => onEdit(patient)} />,
        patientDocument(patient.document_type, patient.document_number),
        patient.phone ?? 'Sin teléfono',
        patient.email ?? 'Sin email',
        <Badge tone={patientStatusTone(patient.profile_status)}>{patientStatusLabel(patient.profile_status)}</Badge>,
        patient.profile_status === 'inactive' ? (
          <Button type="button" variant="secondary" className="px-3 py-1.5" disabled={actionPending} onClick={() => window.confirm(`¿Reactivar ${patient.full_name}?`) && onReactivate(patient)}>Reactivar</Button>
        ) : (
          <Button type="button" variant="danger" className="px-3 py-1.5" disabled={actionPending} onClick={() => window.confirm(`¿Inactivar ${patient.full_name}? No se eliminará físicamente.`) && onDisable(patient)}>Inactivar</Button>
        ),
      ])}
    />
  );
}
