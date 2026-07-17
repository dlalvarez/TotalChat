import { useEffect, useMemo, useState } from 'react';
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
import { RoomsPage } from './features/rooms/RoomsPage';
import { PractitionersPage } from './features/practitioners/PractitionersPage';
import { SpecialtiesPage } from './features/specialties/SpecialtiesPage';
import { OrganizationPractitionersPage } from './features/organizationPractitioners/OrganizationPractitionersPage';
import { PractitionerServicesPage } from './features/practitionerServices/PractitionerServicesPage';
import { PayersAndPlansPage } from './features/payers/PayersAndPlansPage';
import { PricesPage } from './features/prices/PricesPage';
import { AvailabilityPage } from './features/availability/AvailabilityPage';
import { AppointmentsPage } from './features/appointments/AppointmentsPage';
import { PatientsPage } from './features/patients/PatientsPage';
import { PaymentsPage } from './features/payments/PaymentsPage';
import { getMe, type AuthUser } from './api/auth';
import type { AdminTenant } from './config/tenant';

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
        title={`${name} · diferido a fases posteriores`}
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
  const [user, setUser] = useState<AuthUser | null>(null);
  const [active, setActive] = useState('Dashboard');
  const [tenant, setTenant] = useState<AdminTenant | null>(null);
  const queryClient = useMemo(() => new QueryClient(), []);

  useEffect(() => {
    const token = window.localStorage.getItem('totalchat_admin_access_token');
    if (!token) return;
    getMe(token)
      .then((loadedUser) => {
        setUser(loadedUser);
        const firstTenant = loadedUser.tenants[0];
        if (firstTenant) setTenant({ id: firstTenant.tenant_id, label: firstTenant.tenant_name, role: firstTenant.role });
      })
      .catch(() => window.localStorage.removeItem('totalchat_admin_access_token'));
  }, []);

  function logout() {
    window.localStorage.removeItem('totalchat_admin_access_token');
    setUser(null);
    setTenant(null);
    setActive('Dashboard');
  }

  if (!user || !tenant) {
    return (
      <QueryClientProvider client={queryClient}>
        <LoginPage onLogin={(_token, loadedUser) => {
          setUser(loadedUser);
          const firstTenant = loadedUser.tenants[0];
          if (firstTenant) setTenant({ id: firstTenant.tenant_id, label: firstTenant.tenant_name, role: firstTenant.role });
        }} />
      </QueryClientProvider>
    );
  }

  return (
    <QueryClientProvider client={queryClient}>
      <div className="bg-white px-4 py-2 text-right text-sm">
        {user.tenants.length > 1 ? (
          <select className="mr-3 rounded-lg border border-slate-200 px-3 py-2" value={tenant.id} onChange={(event) => {
            const selected = user.tenants.find((item) => item.tenant_id === event.target.value);
            if (selected) setTenant({ id: selected.tenant_id, label: selected.tenant_name, role: selected.role });
          }}>
            {user.tenants.map((item) => <option key={item.tenant_id} value={item.tenant_id}>{item.tenant_name} · {item.role}</option>)}
          </select>
        ) : null}
        <Button variant="secondary" onClick={logout}>Cerrar sesión</Button>
      </div>
      <AdminLayout active={active} onNavigate={setActive} tenantLabel={tenant.label}>
        {active === 'Dashboard' ? <DashboardPage /> : null}
        {active === 'Organizaciones' ? <OrganizationsPage tenant={tenant} /> : null}
        {active === 'Sedes' ? <LocationsPage tenant={tenant} /> : null}
        {active === 'Consultorios' ? <RoomsPage tenant={tenant} /> : null}
        {active === 'Profesionales' ? <PractitionersPage tenant={tenant} /> : null}
        {active === 'Especialidades' ? <SpecialtiesPage tenant={tenant} /> : null}
        {active === 'Profesionales por organización' ? <OrganizationPractitionersPage tenant={tenant} /> : null}
        {active === 'Servicios' ? <PractitionerServicesPage tenant={tenant} /> : null}
        {active === 'Pagadores y planes' ? <PayersAndPlansPage tenant={tenant} /> : null}
        {active === 'Precios' ? <PricesPage tenant={tenant} /> : null}
        {active === 'Disponibilidad' ? <AvailabilityPage tenant={tenant} /> : null}
        {active === 'Pacientes' ? <PatientsPage tenant={tenant} /> : null}
        {active === 'Citas' ? <AppointmentsPage tenant={tenant} /> : null}
        {active === 'Pagos' ? <PaymentsPage tenant={tenant} /> : null}
        {!['Dashboard', 'Organizaciones', 'Sedes', 'Consultorios', 'Profesionales', 'Especialidades', 'Profesionales por organización', 'Servicios', 'Pagadores y planes', 'Precios', 'Disponibilidad', 'Pacientes', 'Citas', 'Pagos'].includes(active) ? <PlaceholderPage name={active} /> : null}
      </AdminLayout>
    </QueryClientProvider>
  );
}
