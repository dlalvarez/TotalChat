export const PAYMENT_METHOD_OPTIONS = [
  { value: '', label: 'Todos' }, { value: 'transfer', label: 'Transferencia' }, { value: 'simulated', label: 'Simulado' }, { value: 'pay_on_site', label: 'Pago en sitio' },
];
export const PAYMENT_STATUS_OPTIONS = [
  { value: '', label: 'Todos' }, { value: 'pending', label: 'Pendiente' }, { value: 'evidence_required', label: 'Esperando evidencia' }, { value: 'evidence_received', label: 'Evidencia recibida' }, { value: 'under_review', label: 'En revisión' }, { value: 'approved', label: 'Aprobado' }, { value: 'rejected', label: 'Rechazado' }, { value: 'expired', label: 'Vencido' }, { value: 'cancelled', label: 'Cancelado' }, { value: 'simulated_approved', label: 'Simulado aprobado' },
];
export const paymentMethodLabel = (v: string) => PAYMENT_METHOD_OPTIONS.find((o) => o.value === v)?.label ?? v;
export const paymentStatusLabel = (v: string) => PAYMENT_STATUS_OPTIONS.find((o) => o.value === v)?.label ?? v;
export const paymentStatusTone = (v: string) => v === 'approved' || v === 'simulated_approved' ? 'success' : v === 'rejected' || v === 'expired' || v === 'cancelled' ? 'warning' : v === 'evidence_received' || v === 'under_review' ? 'info' : 'neutral';
export const isReviewablePayment = (status: string, method: string) => method === 'transfer' && status === 'evidence_received';
export const formatMoney = (amount: number, currency: string) => new Intl.NumberFormat('es-CO', { style: 'currency', currency: currency || 'COP', maximumFractionDigits: 0 }).format(amount || 0);
export const formatDateTime = (value: string | null) => value ? new Intl.DateTimeFormat('es-CO', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value)) : '—';
