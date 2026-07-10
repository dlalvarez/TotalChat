import { ReactNode, useState } from 'react';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { cn } from '../../lib/utils';

const nav = [
  'Dashboard',
  'Organizaciones',
  'Sedes',
  'Consultorios',
  'Profesionales',
  'Especialidades',
  'Profesionales por organización',
  'Servicios',
  'Precios',
  'Pagadores y planes',
  'Disponibilidad',
  'Citas',
  'Pagos',
  'Configuración',
];

export function AdminLayout({
  children,
  active = 'Dashboard',
  onNavigate,
  tenantLabel = 'Clínica demo',
}: {
  children: ReactNode;
  active?: string;
  onNavigate: (item: string) => void;
  tenantLabel?: string;
}) {
  const [open, setOpen] = useState(false);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 lg:grid lg:grid-cols-[280px_1fr]">
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-40 w-72 border-r border-slate-200 bg-white p-5 transition lg:static lg:block',
          open ? 'translate-x-0' : '-translate-x-full lg:translate-x-0',
        )}
      >
        <div className="mb-8 flex items-center gap-3">
          <div className="grid h-11 w-11 place-items-center rounded-2xl bg-brand-600 font-bold text-white">
            TC
          </div>
          <div>
            <p className="font-bold text-slate-950">TotalChat</p>
            <p className="text-xs text-slate-500">MediChat Admin MVP</p>
          </div>
        </div>

        <nav className="space-y-1">
          {nav.map((item) => (
            <button
              key={item}
              onClick={() => {
                onNavigate(item);
                setOpen(false);
              }}
              className={cn(
                'flex w-full items-center justify-between rounded-xl px-3 py-2.5 text-left text-sm font-medium transition',
                active === item
                  ? 'bg-brand-50 text-brand-700'
                  : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900',
              )}
            >
              <span>{item}</span>
              {item === 'Configuración' ? <Badge>Base</Badge> : null}
            </button>
          ))}
        </nav>

        <div className="mt-6 rounded-2xl bg-slate-50 p-4 text-xs text-slate-500">
          <strong className="text-slate-700">Fase 6B.5:</strong> relación Organización–Profesional funcional; Servicios sigue diferido.
        </div>
      </aside>

      <div className="min-w-0">
        <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/90 px-4 py-3 backdrop-blur lg:px-8">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <Button variant="secondary" className="lg:hidden" onClick={() => setOpen(true)}>
                Menú
              </Button>
              <div>
                <p className="text-sm text-slate-500">Tenant activo</p>
                <p className="font-semibold text-slate-950">{tenantLabel} · selector dev</p>
              </div>
            </div>
            <div className="hidden items-center gap-3 sm:flex">
              <Badge tone="info">JWT futuro</Badge>
              <Button variant="ghost">Soporte</Button>
            </div>
          </div>
        </header>
        <main className="px-4 py-6 lg:px-8">{children}</main>
      </div>
    </div>
  );
}
