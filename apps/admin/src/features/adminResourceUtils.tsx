import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';

export function StatusBadge({ status, feminine = false }: { status: string; feminine?: boolean }) {
  const active = status === 'active';
  return <Badge tone={active ? 'success' : 'neutral'}>{active ? (feminine ? 'Activa' : 'Activo') : (feminine ? 'Inactiva' : 'Inactivo')}</Badge>;
}

export function NameEditButton({ name, onEdit }: { name: string; onEdit: () => void }) {
  return (
    <Button type="button" variant="ghost" className="h-auto justify-start px-0 py-0 text-left font-semibold text-brand-700 hover:bg-transparent hover:text-brand-800" onClick={onEdit}>
      {name}
    </Button>
  );
}

export function StatusAction({ status, entityName, onActivate, onInactivate, disabled }: { status: string; entityName: string; onActivate: () => void; onInactivate: () => void; disabled?: boolean }) {
  const active = status === 'active';
  const label = active ? 'Inactivar' : 'Activar';
  const message = active ? `¿Inactivar ${entityName}? No se eliminará físicamente.` : `¿Activar ${entityName} nuevamente?`;

  return (
    <Button
      type="button"
      variant={active ? 'danger' : 'secondary'}
      className="px-3 py-1.5"
      disabled={disabled}
      onClick={() => {
        if (window.confirm(message)) {
          if (active) {
            onInactivate();
          } else {
            onActivate();
          }
        }
      }}
    >
      {label}
    </Button>
  );
}
