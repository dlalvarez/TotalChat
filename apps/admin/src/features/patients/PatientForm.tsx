import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { Button } from '../../components/ui/Button';
import { FieldWrapper, Input, Select } from '../../components/ui/Form';
import type { CreatePatientPayload, Patient, PatientDocumentType, UpdatePatientPayload } from '../../api/adminResources';
import { emptyToNull } from '../adminResourceFormat';
import { PATIENT_DOCUMENT_TYPE_OPTIONS, PATIENT_PROFILE_OPTIONS } from './patientUtils';

const schema = z.object({
  full_name: z.string().min(1, 'El nombre completo es obligatorio'),
  document_type: z.enum(['', 'RC', 'TI', 'CC', 'PAS', 'CE', 'RE', 'PPT', 'SC', 'DNI', 'NIT', 'OTHER']).optional(),
  document_number: z.string().optional(),
  phone: z.string().optional(),
  email: z.string().email('Email inválido').or(z.literal('')).optional(),
  profile_status: z.enum(['minimal', 'incomplete', 'complete', 'verified', 'inactive']).optional(),
});

type FormValues = z.infer<typeof schema>;

const defaults = (patient?: Patient): FormValues => ({
  full_name: patient?.full_name ?? '',
  document_type: patient?.document_type ?? '',
  document_number: patient?.document_number ?? '',
  phone: patient?.phone ?? '',
  email: patient?.email ?? '',
  profile_status: patient?.profile_status ?? 'minimal',
});

export function PatientForm({ patient, pending, onCancel, onSubmit }: { patient?: Patient | null; pending?: boolean; onCancel: () => void; onSubmit: (payload: CreatePatientPayload | UpdatePatientPayload) => void }) {
  const form = useForm<FormValues>({ resolver: zodResolver(schema), defaultValues: defaults(patient ?? undefined) });

  useEffect(() => {
    form.reset(defaults(patient ?? undefined));
  }, [form, patient]);

  return (
    <form className="grid gap-4 md:grid-cols-2" onSubmit={form.handleSubmit((values) => onSubmit({
      full_name: values.full_name.trim(),
      document_type: emptyToNull(values.document_type) as PatientDocumentType | null,
      document_number: emptyToNull(values.document_number),
      phone: emptyToNull(values.phone),
      email: emptyToNull(values.email),
      ...(patient ? { profile_status: values.profile_status } : {}),
    }))}>
      <FieldWrapper label="Nombre completo" error={form.formState.errors.full_name?.message}>
        <Input placeholder="Juan Pérez" {...form.register('full_name')} />
      </FieldWrapper>
      <FieldWrapper label="Tipo de documento" error={form.formState.errors.document_type?.message}>
        <Select {...form.register('document_type')}>
          <option value="">Sin tipo de documento</option>
          {PATIENT_DOCUMENT_TYPE_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
        </Select>
      </FieldWrapper>
      <FieldWrapper label="Número de documento" error={form.formState.errors.document_number?.message}>
        <Input placeholder="123456789" {...form.register('document_number')} />
      </FieldWrapper>
      <FieldWrapper label="Teléfono" error={form.formState.errors.phone?.message}>
        <Input placeholder="+573001112233" {...form.register('phone')} />
      </FieldWrapper>
      <FieldWrapper label="Email" error={form.formState.errors.email?.message}>
        <Input placeholder="juan@example.com" {...form.register('email')} />
      </FieldWrapper>
      {patient ? (
        <FieldWrapper label="Estado del perfil" error={form.formState.errors.profile_status?.message}>
          <Select {...form.register('profile_status')}>
            {PATIENT_PROFILE_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
          </Select>
        </FieldWrapper>
      ) : null}
      <div className="flex gap-2 md:col-span-2">
        <Button type="submit" disabled={pending}>{pending ? 'Guardando…' : 'Guardar paciente'}</Button>
        <Button type="button" variant="secondary" onClick={onCancel}>Cancelar</Button>
      </div>
    </form>
  );
}
