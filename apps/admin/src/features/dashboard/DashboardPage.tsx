import { useQuery } from '@tanstack/react-query';
import { Badge } from '../../components/ui/Badge';
import { DataTableShell } from '../../components/ui/DataTable';
import { EmptyState, ErrorState, LoadingState } from '../../components/ui/States';
import { PageHeader } from '../../components/layout/PageHeader';
import { Card, SectionCard } from '../../components/ui/Card';
import { adminDashboardApi, type DashboardSummary } from '../../api/adminResources';
import type { AdminTenant } from '../../config/tenant';
import { formatDateTime } from '../payments/paymentUtils';

const metricCards: Array<[keyof DashboardSummary['metrics'], string, string, 'info' | 'warning' | 'success' | 'neutral']> = [
  ['appointments_today', 'Citas de hoy', 'Agenda del día actual', 'info'],
  ['upcoming_appointments', 'Próximas scheduled', 'Citas futuras programadas', 'info'],
  ['appointments_pending_payment', 'Pendientes de pago', 'Citas con pago pendiente', 'warning'],
  ['payment_reviews_pending', 'Pagos por revisar', 'Transferencias con evidencia', 'warning'],
  ['virtual_appointments_without_link', 'Virtuales sin link', 'Requieren enlace manual', 'warning'],
  ['active_services', 'Servicios activos', 'Catálogo operativo', 'success'],
  ['active_practitioners', 'Profesionales activos', 'Equipo disponible', 'success'],
];

const paymentStatusTone = (status: string) => (status === 'paid' ? 'success' : status === 'pending' ? 'warning' : 'neutral');
const money = (amount: number | null, currency: string) => amount === null ? `— ${currency}` : new Intl.NumberFormat('es-CO', { style: 'currency', currency }).format(amount);

export function DashboardPage({ tenant }: { tenant: AdminTenant }) {
  const summary = useQuery({ queryKey: ['dashboard-summary', tenant.id], queryFn: () => adminDashboardApi.getSummary(tenant.id) });
  const data = summary.data;

  return (
    <>
      <PageHeader
        eyebrow="Fase 6D.1 · dashboard real"
        title="Dashboard administrativo"
        description="Resumen operativo tenant-scoped con citas, pagos, links virtuales, servicios y profesionales reales del tenant actual."
      />

      {summary.isLoading ? <LoadingState label="Cargando resumen operativo…" /> : null}
      {summary.isError ? <ErrorState description={(summary.error as Error).message} /> : null}

      {data ? (
        <>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {metricCards.map(([key, label, description, tone]) => (
              <Card key={key}>
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm text-slate-500">{label}</p>
                    <p className="mt-2 text-3xl font-bold text-slate-950">{data.metrics[key]}</p>
                    <p className="mt-1 text-xs text-slate-500">{description}</p>
                  </div>
                  <Badge tone={tone}>{tone === 'warning' ? 'Revisar' : 'Real'}</Badge>
                </div>
              </Card>
            ))}
          </div>

          <div className="mt-6 grid gap-6 xl:grid-cols-[1.2fr_1fr]">
            <SectionCard title="Agenda de hoy" description="Próximas citas del día actual para el tenant seleccionado.">
              {data.today_appointments.length === 0 ? <EmptyState title="Sin citas próximas hoy" description="No hay citas restantes para hoy en el tenant actual." /> : null}
              {data.today_appointments.length > 0 ? <DataTableShell columns={['Hora', 'Paciente', 'Atención', 'Estado']} rows={data.today_appointments.map((item) => [
                formatDateTime(item.starts_at),
                <strong>{item.patient_name}</strong>,
                `${item.service_name} · ${item.practitioner_name} · ${item.location_name ?? 'Sin sede'}`,
                <div className="flex flex-wrap gap-2"><Badge tone="info">{item.status}</Badge><Badge tone={paymentStatusTone(item.payment_status)}>{item.payment_status}</Badge></div>,
              ])} /> : null}
            </SectionCard>

            <SectionCard title="Pagos pendientes de revisión" description="Transferencias con evidencia recibida que esperan decisión manual.">
              {data.pending_payment_reviews.length === 0 ? <EmptyState title="Sin pagos por revisar" description="No hay evidencias de transferencia pendientes de revisión." /> : null}
              {data.pending_payment_reviews.length > 0 ? <DataTableShell columns={['Recibido', 'Paciente', 'Servicio', 'Monto']} rows={data.pending_payment_reviews.map((item) => [
                item.evidence_received_at ? formatDateTime(item.evidence_received_at) : 'Sin fecha',
                <strong>{item.patient_name}</strong>,
                `${item.service_name} · ${item.practitioner_name}`,
                money(item.amount, item.currency),
              ])} /> : null}
            </SectionCard>

            <SectionCard title="Alertas de links virtuales" description="Citas virtuales scheduled sin URL de reunión manual registrada.">
              {data.virtual_link_alerts.length === 0 ? <EmptyState title="Sin links virtuales pendientes" description="Todas las citas virtuales programadas tienen link o no requieren uno." /> : null}
              {data.virtual_link_alerts.length > 0 ? <DataTableShell columns={['Fecha', 'Paciente', 'Atención', 'Sede']} rows={data.virtual_link_alerts.map((item) => [
                formatDateTime(item.starts_at),
                <strong>{item.patient_name}</strong>,
                `${item.service_name} · ${item.practitioner_name}`,
                item.location_name ?? 'Teleconsulta',
              ])} /> : null}
            </SectionCard>
          </div>
        </>
      ) : null}
    </>
  );
}
