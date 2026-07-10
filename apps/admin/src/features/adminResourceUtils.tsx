import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';

export function StatusBadge({ status, feminine = false }: { status: string; feminine?: boolean }) {
  const active = status === 'active';
  return <Badge tone={active ? 'success' : 'neutral'}>{active ? (feminine ? 'Activa' : 'Activo') : (feminine ? 'Inactiva' : 'Inactivo')}</Badge>;
}

export function NameEditButton({ children, onClick }: { children: string; onClick: () => void }) {
  return (
    <button type="button" className="font-semibold text-brand-700 underline-offset-4 transition hover:text-brand-800 hover:underline" onClick={onClick}>
      {children}
    </button>
  );
}

export function StatusAction({ status, onActivate, onDeactivate, pending }: { status: string; onActivate: () => void; onDeactivate: () => void; pending?: boolean }) {
  const active = status === 'active';
  return (
    <Button type="button" variant={active ? 'danger' : 'secondary'} className="px-3 py-1.5" disabled={pending} onClick={active ? onDeactivate : onActivate}>
      {active ? 'Inactivar' : 'Activar'}
    </Button>
  );
}
