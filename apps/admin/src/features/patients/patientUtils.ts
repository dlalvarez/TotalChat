import type { PatientDocumentType, PatientProfileStatus } from '../../api/adminResources';


export const PATIENT_DOCUMENT_TYPE_OPTIONS: { value: PatientDocumentType; label: string }[] = [
  { value: 'RC', label: 'Registro Civil de Nacimiento' },
  { value: 'TI', label: 'Tarjeta de Identidad' },
  { value: 'CC', label: 'Cédula de Ciudadanía' },
  { value: 'PAS', label: 'Pasaporte' },
  { value: 'CE', label: 'Cédula de Extranjería' },
  { value: 'RE', label: 'Registro de Extranjeros' },
  { value: 'PPT', label: 'Permiso por Protección Temporal' },
  { value: 'SC', label: 'Salvoconducto' },
  { value: 'DNI', label: 'Documento Nacional de Identidad CAN/MERCOSUR' },
  { value: 'NIT', label: 'NIT' },
  { value: 'OTHER', label: 'Otro' },
];

export const patientDocumentTypeLabel = (documentType?: string | null) => PATIENT_DOCUMENT_TYPE_OPTIONS.find((option) => option.value === documentType)?.label ?? documentType ?? 'Sin tipo de documento';

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
