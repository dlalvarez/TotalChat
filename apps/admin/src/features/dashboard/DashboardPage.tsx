import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { DataTableShell } from '../../components/ui/DataTable';
import { EmptyState } from '../../components/ui/States';
import { FieldWrapper, SearchInput, SearchableSelectPlaceholder, Select } from '../../components/ui/Form';
import { PageHeader } from '../../components/layout/PageHeader';
import { Card, SectionCard } from '../../components/ui/Card';

const metrics = [
  ['Citas de hoy', '18', 'info'], ['Citas pendientes de pago', '7', 'warning'], ['Pagos pendientes de revisión', '4', 'warning'], ['Revisiones vencidas', '2', 'warning'], ['Citas sin confirmación', '9', 'neutral'], ['Profesionales activos', '12', 'success'], ['Servicios activos', '34', 'success'],
] as const;

export function DashboardPage() { return <><PageHeader eyebrow="Fase 6A · shell MVP" title="Dashboard administrativo" description="Vista inicial con datos demostrativos no sensibles. Los módulos CRUD completos quedan intencionalmente diferidos para Fase 6B–6E." actions={<><Button variant="secondary">Exportar vista</Button><Button>Nueva acción</Button></>} />
  <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">{metrics.map(([label, value, tone]) => <Card key={label}><div className="flex items-start justify-between gap-3"><div><p className="text-sm text-slate-500">{label}</p><p className="mt-2 text-3xl font-bold text-slate-950">{value}</p></div><Badge tone={tone}>{tone === 'warning' ? 'Revisar' : 'MVP'}</Badge></div></Card>)}</div>
  <div className="mt-6 grid gap-6 xl:grid-cols-[1.4fr_0.8fr]"><SectionCard title="Agenda prioritaria" description="Tabla shell reutilizable para futuras pantallas de citas y pagos."><DataTableShell columns={['Paciente', 'Resumen', 'Estado', 'Acción']} rows={[[<strong>Paciente demo</strong>, 'Hoy 10:30 · Psicología · Dra. Ana Ruiz', <Badge tone="warning">Pago pendiente</Badge>, <Button variant="secondary">Ver detalle</Button>], ['Paciente ejemplo', 'Hoy 14:00 · Medicina general · Dr. Carlos Mejía', <Badge tone="success">Confirmada</Badge>, <Button variant="secondary">Ver detalle</Button>]]} /></SectionCard><SectionCard title="Patrones UX reutilizables" description="Relaciones por etiquetas legibles, nunca captura manual de UUIDs."><div className="space-y-4"><SearchInput /><FieldWrapper label="Profesional"><Select><option>Dra. Ana Ruiz · Psicología</option><option>Dr. Carlos Mejía · Medicina general</option></Select></FieldWrapper><SearchableSelectPlaceholder /><EmptyState title="Sin campañas implementadas" description="Los módulos fuera de Fase 6A permanecen deshabilitados u omitidos hasta su fase correspondiente." /></div></SectionCard></div></>; }
