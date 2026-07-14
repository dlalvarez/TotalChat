import type { PatientProfileStatus } from '../../api/adminResources';

export const PATIENT_PROFILE_OPTIONS: { value: PatientProfileStatus; label: string }[] = [
  { value: 'minimal', label: 'Mínimo' },
  { value: 'incomplete', label: 'Incompleto' },
  { value: 'complete', label: 'Completo' },
  { value: 'verified', label: 'Verificado' },
  { value: 'inactive', label: 'Inactivo' },
];

export const patientStatusLabel = (status: PatientProfileStatus | string) => PATIENT_PROFILE_OPTIONS.find((option) => option.value === status)?.label ?? status;

export const patientStatusTone = (status: PatientProfileStatus | string) => {
  if (status === 'verified' || status === 'complete') return 'success';
  if (status === 'minimal') return 'warning';
  if (status === 'incomplete') return 'info';
  return 'neutral';
};

export const patientDocument = (documentType?: string | null, documentNumber?: string | null) => [documentType, documentNumber].filter(Boolean).join(' ') || 'Sin documento';
