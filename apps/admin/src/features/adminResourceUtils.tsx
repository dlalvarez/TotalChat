import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';

export function StatusBadge({ status, feminine = false }: { status: string; feminine?: boolean }) {
  const active = status === 'active';
  return <Badge tone={active ? 'success' : 'neutral'}>{active ? (feminine ? 'Activa' : 'Activo') : (feminine ? 'Inactiva' : 'Inactivo')}</Badge>;
}

export function RowActions({ onEdit, onDisable, disabled }: { onEdit: () => void; onDisable: () => void; disabled?: boolean }) {
  return (
    <div className="flex flex-wrap gap-2">
      <Button type="button" variant="secondary" className="px-3 py-1.5" onClick={onEdit}>Editar</Button>
      <Button type="button" variant="danger" className="px-3 py-1.5" disabled={disabled} onClick={onDisable}>Inactivar</Button>
    </div>
  );
}
