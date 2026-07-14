import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { PageHeader } from '../../components/layout/PageHeader';
import { SectionCard } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { FieldWrapper, Input, Select } from '../../components/ui/Form';
import { EmptyState, ErrorState, LoadingState } from '../../components/ui/States';
import { adminPaymentsApi, adminResourcesApi, type AdminPayment, type PaymentFilters } from '../../api/adminResources';
import type { AdminTenant } from '../../config/tenant';
import { PaymentList } from './PaymentList';
import { PaymentDetailPanel } from './PaymentDetailPanel';
import { formatDateTime, PAYMENT_METHOD_OPTIONS, PAYMENT_STATUS_OPTIONS, paymentStatusLabel } from './paymentUtils';

type FilterState = Required<Pick<PaymentFilters, 'organization_id' | 'status' | 'method' | 'date_from' | 'date_to' | 'patient'>>;
type ManualPaymentForm = { booking_id: string; amount: string; evidence_reference: string; evidence_notes: string };

const defaultManualPayment: ManualPaymentForm = { booking_id: '', amount: '', evidence_reference: '', evidence_notes: '' };

export function PaymentsPage({ tenant }: { tenant: AdminTenant }) {
  const [filters, setFilters] = useState<FilterState>({ organization_id: '', status: '', method: '', date_from: '', date_to: '', patient: '' });
  const [selected, setSelected] = useState<AdminPayment | null>(null);
  const [showManualForm, setShowManualForm] = useState(false);
  const [manualPayment, setManualPayment] = useState<ManualPaymentForm>(defaultManualPayment);
  const qc = useQueryClient();
  const apiFilters = useMemo(() => Object.fromEntries(Object.entries(filters).filter(([, v]) => v)) as PaymentFilters, [filters]);
  const payments = useQuery({ queryKey: ['payments', tenant.id, apiFilters], queryFn: () => adminPaymentsApi.listPayments(tenant.id, apiFilters) });
  const organizations = useQuery({ queryKey: ['organizations', tenant.id], queryFn: () => adminResourcesApi.listOrganizations(tenant.id) });
  const appointments = useQuery({ queryKey: ['appointments', tenant.id, 'payments-manual'], queryFn: () => adminResourcesApi.listAppointments(tenant.id) });
  const detail = useQuery({ queryKey: ['payments', tenant.id, selected?.id, 'detail'], queryFn: () => adminPaymentsApi.getPayment(tenant.id, selected!.id), enabled: Boolean(selected?.id) });
  const invalidate = async () => { await qc.invalidateQueries({ queryKey: ['payments', tenant.id] }); };
  const approve = useMutation({ mutationFn: (payment: AdminPayment) => adminPaymentsApi.approvePayment(tenant.id, payment.id), onSuccess: async (data) => { setSelected(data); await invalidate(); } });
  const reject = useMutation({ mutationFn: ({ payment, reason }: { payment: AdminPayment; reason: string }) => adminPaymentsApi.rejectPayment(tenant.id, payment.id, reason), onSuccess: async (data) => { setSelected(data); await invalidate(); } });
  const createManual = useMutation({
    mutationFn: async (form: ManualPaymentForm) => {
      const attempt = await adminPaymentsApi.createTransferPaymentAttempt(tenant.id, { booking_id: form.booking_id, amount: form.amount, currency: 'COP' });
      const reference = form.evidence_reference.trim();
      const notes = form.evidence_notes.trim();
      if (reference || notes) {
        await adminPaymentsApi.registerPaymentEvidence(tenant.id, attempt.id, {
          original_filename: reference || 'referencia-manual',
          uploaded_channel: 'admin',
          notes: notes || reference,
        });
      }
      return attempt;
    },
    onSuccess: async () => {
      setManualPayment(defaultManualPayment);
      setShowManualForm(false);
      await invalidate();
    },
  });
  const rows = payments.data ?? [];
  const summary = {
    total: rows.length,
    review: rows.filter((p) => p.method === 'transfer' && p.status === 'evidence_received').length,
    approved: rows.filter((p) => ['approved', 'simulated_approved'].includes(p.status)).length,
    rejected: rows.filter((p) => p.status === 'rejected').length,
    expired: rows.filter((p) => p.status === 'expired').length,
  };
  const activeDetail = detail.data ?? selected ?? undefined;
  const appointmentOptions = (appointments.data ?? []).map((appointment) => ({
    value: appointment.id,
    label: `${appointment.patient_name ?? 'Paciente'} · ${formatDateTime(appointment.starts_at)} · ${appointment.practitioner_name ?? 'Profesional'} · ${appointment.practitioner_service_name ?? 'Servicio'}`,
  }));
  return <><PageHeader eyebrow="Fase 6B.11" title="Pagos" description="Consulta intentos de pago asociados a citas y registra revisión manual básica sin pasarelas, webhooks ni conciliación bancaria." actions={<Button onClick={() => setShowManualForm((value) => !value)}>Registrar pago manual</Button>} />
    <div className="grid gap-4 md:grid-cols-5">{[['Total', summary.total], ['Pendientes de revisión', summary.review], ['Aprobados', summary.approved], ['Rechazados', summary.rejected], ['Vencidos sin evidencia', summary.expired]].map(([label, value]) => <SectionCard key={label} title={String(value)} description={String(label)}><span className="text-xs text-slate-500">{label === 'Pendientes de revisión' ? 'Transferencias con evidencia recibida' : label === 'Vencidos sin evidencia' ? 'No aprobables directamente' : 'Resumen operativo'}</span></SectionCard>)}</div>
    <SectionCard title="Filtros" description="La búsqueda usa nombres legibles; UUIDs y schema del tenant permanecen internos."><div className="grid gap-4 md:grid-cols-3 lg:grid-cols-6"><FieldWrapper label="Organización"><Select value={filters.organization_id} onChange={(e) => setFilters({ ...filters, organization_id: e.target.value })}><option value="">Todas</option>{(organizations.data ?? []).map((o) => <option key={o.id} value={o.id}>{o.name}</option>)}</Select></FieldWrapper><FieldWrapper label="Método"><Select value={filters.method} onChange={(e) => setFilters({ ...filters, method: e.target.value })}>{PAYMENT_METHOD_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}</Select></FieldWrapper><FieldWrapper label="Estado"><Select value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value })}>{PAYMENT_STATUS_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}</Select></FieldWrapper><FieldWrapper label="Desde"><Input type="date" value={filters.date_from} onChange={(e) => setFilters({ ...filters, date_from: e.target.value })} /></FieldWrapper><FieldWrapper label="Hasta"><Input type="date" value={filters.date_to} onChange={(e) => setFilters({ ...filters, date_to: e.target.value })} /></FieldWrapper><FieldWrapper label="Paciente"><Input value={filters.patient} onChange={(e) => setFilters({ ...filters, patient: e.target.value })} placeholder="Nombre o documento" /></FieldWrapper></div></SectionCard>
    {showManualForm ? <SectionCard title="Registrar pago manual" description="Crea un intento transfer pendiente o con evidencia recibida usando servicios existentes. No aprueba pagos automáticamente.">{createManual.isError ? <ErrorState description={(createManual.error as Error).message} /> : null}{appointments.isLoading ? <LoadingState label="Cargando citas…" /> : null}{appointments.isSuccess && appointmentOptions.length === 0 ? <EmptyState title="Sin citas disponibles" description="Crea una cita administrativa antes de registrar un intento de pago manual." /> : null}{appointmentOptions.length > 0 ? <form className="grid gap-4 lg:grid-cols-[2fr_1fr_1fr]" onSubmit={(event) => { event.preventDefault(); createManual.mutate(manualPayment); }}><FieldWrapper label="Cita"><Select value={manualPayment.booking_id} onChange={(e) => setManualPayment({ ...manualPayment, booking_id: e.target.value })} required><option value="">Selecciona paciente · fecha · profesional · servicio</option>{appointmentOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}</Select></FieldWrapper><FieldWrapper label="Monto COP"><Input type="number" min="0" step="0.01" value={manualPayment.amount} onChange={(e) => setManualPayment({ ...manualPayment, amount: e.target.value })} required /></FieldWrapper><FieldWrapper label="Método"><Input value="Transferencia" disabled /></FieldWrapper><FieldWrapper label="Referencia de comprobante"><Input value={manualPayment.evidence_reference} onChange={(e) => setManualPayment({ ...manualPayment, evidence_reference: e.target.value })} placeholder="Opcional: número o nombre de comprobante" /></FieldWrapper><FieldWrapper label="Notas de evidencia"><Input value={manualPayment.evidence_notes} onChange={(e) => setManualPayment({ ...manualPayment, evidence_notes: e.target.value })} placeholder="Opcional" /></FieldWrapper><div className="flex items-end gap-2"><Button type="submit" disabled={createManual.isPending || !manualPayment.booking_id || !manualPayment.amount}>{createManual.isPending ? 'Registrando…' : 'Registrar intento'}</Button><Button type="button" variant="secondary" onClick={() => { setManualPayment(defaultManualPayment); setShowManualForm(false); }}>Cancelar</Button></div><p className="text-xs text-slate-500 lg:col-span-3">Si agregas referencia o notas de evidencia, el intento pasa por el flujo de evidencia existente y queda listo para revisión manual. Si no, queda esperando evidencia.</p></form> : null}</SectionCard> : null}
    <div className="grid gap-6 xl:grid-cols-[1.4fr_1fr]"><SectionCard title="Listado de pagos" description="Intentos asociados a citas del tenant actual.">{payments.isLoading ? <LoadingState label="Cargando pagos…" /> : null}{payments.isError ? <ErrorState description={(payments.error as Error).message} /> : null}{payments.isSuccess && rows.length === 0 ? <EmptyState title="Sin pagos" description="No hay intentos con los filtros seleccionados." /> : null}{rows.length > 0 ? <PaymentList payments={rows} selectedId={selected?.id} onSelect={setSelected} /> : null}</SectionCard><SectionCard title="Detalle y revisión" description="La aprobación o rechazo solo actualiza pago y estado de pago de la cita; no confirma, cancela ni libera cupos. Los vencidos por falta de evidencia no son aprobables directamente.">{approve.isError ? <ErrorState description={(approve.error as Error).message} /> : null}{reject.isError ? <ErrorState description={(reject.error as Error).message} /> : null}<PaymentDetailPanel payment={activeDetail} isLoading={detail.isLoading} isActionPending={approve.isPending || reject.isPending} onApprove={() => activeDetail && approve.mutate(activeDetail)} onReject={(reason) => activeDetail && reject.mutate({ payment: activeDetail, reason })} /></SectionCard></div></>;
}
