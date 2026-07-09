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

export type Room = {
  id: string;
  location_id: string;
  name: string;
  room_type: string | null;
  capacity: number | null;
  status: string;
};

export type CreateRoomPayload = {
  location_id: string;
  name: string;
  room_type?: string | null;
  capacity?: number | null;
};

export type Practitioner = {
  id: string;
  full_name: string;
  professional_type: string | null;
  professional_license: string | null;
  email: string | null;
  phone: string | null;
  status: string;
};

export type CreatePractitionerPayload = {
  full_name: string;
  professional_type?: string | null;
  professional_license?: string | null;
  email?: string | null;
  phone?: string | null;
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
  listRooms: (tenantId: string) => apiRequest<Room[]>('/api/admin/rooms', { tenantId }),
  createRoom: (tenantId: string, payload: CreateRoomPayload) =>
    apiRequest<Room>('/api/admin/rooms', {
      tenantId,
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  listPractitioners: (tenantId: string) =>
    apiRequest<Practitioner[]>('/api/admin/practitioners', { tenantId }),
  createPractitioner: (tenantId: string, payload: CreatePractitionerPayload) =>
    apiRequest<Practitioner>('/api/admin/practitioners', {
      tenantId,
      method: 'POST',
      body: JSON.stringify(payload),
    }),
};
