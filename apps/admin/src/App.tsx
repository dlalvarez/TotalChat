import { useMemo, useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AdminLayout } from './components/layout/AdminLayout';
import { PageHeader } from './components/layout/PageHeader';
import { SectionCard } from './components/ui/Card';
import { EmptyState, ErrorState, LoadingState } from './components/ui/States';
import { Button } from './components/ui/Button';
import { LoginPage } from './features/auth/LoginPage';
import { DashboardPage } from './features/dashboard/DashboardPage';
import { OrganizationsPage } from './features/organizations/OrganizationsPage';
import { LocationsPage } from './features/locations/LocationsPage';
import { DEFAULT_DEVELOPMENT_TENANT, DEVELOPMENT_TENANTS } from './config/tenant';

function PlaceholderPage({ name }: { name: string }) {
  return (
    <>
      <PageHeader
        eyebrow="Módulo preparado"
        title={name}
        description="Pantalla placeholder profesional para mantener navegación, estados vacíos y patrones visuales mientras el CRUD funcional se implementa en fases posteriores."
        actions={<Button variant="secondary">Acción futura</Button>}
      />
      <SectionCard
        title={`${name} · sin CRUD en Fase 6B.1`}
        description="Este espacio valida shell, jerarquía visual y estados base sin modificar comportamiento backend."
      >
        <div className="grid gap-4 lg:grid-cols-3">
          <EmptyState
            title="Sin registros cargados"
            description="Las listas futuras mostrarán etiquetas legibles, estados y acciones claras."
            actionLabel="Crear en fase futura"
          />
          <LoadingState />
          <ErrorState description="Ejemplo de estado de error reutilizable para integraciones API futuras." />
        </div>
      </SectionCard>
    </>
  );
}

export default function App() {
  const [authenticated, setAuthenticated] = useState(false);
  const [active, setActive] = useState('Dashboard');
  const [tenant, setTenant] = useState(DEFAULT_DEVELOPMENT_TENANT);
  const queryClient = useMemo(() => new QueryClient(), []);

  if (!authenticated) {
    return (
      <QueryClientProvider client={queryClient}>
        <LoginPage onLogin={(tenantId) => {
          setTenant(DEVELOPMENT_TENANTS.find((candidate) => candidate.id === tenantId) ?? DEFAULT_DEVELOPMENT_TENANT);
          setAuthenticated(true);
        }} />
      </QueryClientProvider>
    );
  }

  return (
    <QueryClientProvider client={queryClient}>
      <AdminLayout active={active} onNavigate={setActive} tenantLabel={tenant.label}>
        {active === 'Dashboard' ? <DashboardPage /> : null}
        {active === 'Organizaciones' ? <OrganizationsPage tenant={tenant} /> : null}
        {active === 'Sedes' ? <LocationsPage tenant={tenant} /> : null}
        {!['Dashboard', 'Organizaciones', 'Sedes'].includes(active) ? <PlaceholderPage name={active} /> : null}
      </AdminLayout>
    </QueryClientProvider>
  );
}
