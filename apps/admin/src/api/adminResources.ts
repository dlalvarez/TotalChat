import { apiRequest } from './client';

export type Organization = {
  id: string;
  name: string;
  organization_type: string;
  legal_name: string | null;
  tax_id: string | null;
  email: string | null;
  phone: string | null;
  status: string;
};

export type CreateOrganizationPayload = {
  name: string;
  organization_type: string;
  legal_name?: string | null;
  tax_id?: string | null;
  email?: string | null;
  phone?: string | null;
};

export type Location = {
  id: string;
  organization_id: string;
  name: string;
  address: string | null;
  city: string | null;
  neighborhood: string | null;
  reference: string | null;
  is_virtual: boolean;
  status: string;
};

export type CreateLocationPayload = {
  organization_id: string;
  name: string;
  address?: string | null;
  city?: string | null;
  neighborhood?: string | null;
  reference?: string | null;
  is_virtual: boolean;
};

export const adminResourcesApi = {
  listOrganizations: (tenantId: string) =>
    apiRequest<Organization[]>('/api/admin/organizations', { tenantId }),
  createOrganization: (tenantId: string, payload: CreateOrganizationPayload) =>
    apiRequest<Organization>('/api/admin/organizations', {
      tenantId,
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  listLocations: (tenantId: string) => apiRequest<Location[]>('/api/admin/locations', { tenantId }),
  createLocation: (tenantId: string, payload: CreateLocationPayload) =>
    apiRequest<Location>('/api/admin/locations', {
      tenantId,
      method: 'POST',
      body: JSON.stringify(payload),
    }),
};
