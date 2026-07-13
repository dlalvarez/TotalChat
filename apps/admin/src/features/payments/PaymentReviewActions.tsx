import { useState } from 'react';
import { Button } from '../../components/ui/Button';
import { FieldWrapper, Input } from '../../components/ui/Form';
import type { AdminPayment } from '../../api/adminResources';
import { isReviewablePayment } from './paymentUtils';
export function PaymentReviewActions({ payment, isPending, onApprove, onReject }: { payment: AdminPayment; isPending: boolean; onApprove: () => void; onReject: (reason: string) => void }) {
  const [reason, setReason] = useState(''); const reviewable = isReviewablePayment(payment.status, payment.method);
  if (!reviewable) return <p className="rounded-xl bg-slate-50 p-3 text-sm text-slate-500">Este intento no está en un estado revisable manualmente.</p>;
  return <div className="space-y-3 rounded-2xl border border-slate-200 p-4"><h4 className="font-semibold text-slate-950">Revisión manual</h4><div className="flex flex-wrap gap-2"><Button disabled={isPending} onClick={onApprove}>Aprobar pago</Button></div><div className="grid gap-2 md:grid-cols-[1fr_auto]"><FieldWrapper label="Motivo de rechazo obligatorio"><Input value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Ej. comprobante no corresponde al monto" /></FieldWrapper><div className="flex items-end"><Button variant="danger" disabled={isPending || reason.trim().length === 0} onClick={() => onReject(reason.trim())}>Rechazar</Button></div></div></div>;
}
