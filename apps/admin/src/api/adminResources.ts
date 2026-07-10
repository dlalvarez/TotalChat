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

export type UpsertOrganizationPayload = {
  name?: string;
  organization_type?: string;
  legal_name?: string | null;
  tax_id?: string | null;
  email?: string | null;
  phone?: string | null;
  status?: string;
};
export type CreateOrganizationPayload = Required<Pick<UpsertOrganizationPayload, 'name' | 'organization_type'>> & Omit<UpsertOrganizationPayload, 'name' | 'organization_type' | 'status'>;

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

export type UpsertLocationPayload = {
  organization_id?: string;
  name?: string;
  address?: string | null;
  city?: string | null;
  neighborhood?: string | null;
  reference?: string | null;
  is_virtual?: boolean;
  status?: string;
};
export type CreateLocationPayload = Required<Pick<UpsertLocationPayload, 'organization_id' | 'name' | 'is_virtual'>> & Omit<UpsertLocationPayload, 'organization_id' | 'name' | 'is_virtual' | 'status'>;

export type Room = {
  id: string;
  location_id: string;
  name: string;
  room_type: string | null;
  capacity: number | null;
  status: string;
};

export type UpsertRoomPayload = {
  location_id?: string;
  name?: string;
  room_type?: string | null;
  capacity?: number | null;
  status?: string;
};
export type CreateRoomPayload = Required<Pick<UpsertRoomPayload, 'location_id' | 'name'>> & Omit<UpsertRoomPayload, 'location_id' | 'name' | 'status'>;

export type Practitioner = {
  id: string;
  full_name: string;
  professional_type: string | null;
  professional_license: string | null;
  email: string | null;
  phone: string | null;
  status: string;
};

export type UpsertPractitionerPayload = {
  full_name?: string;
  professional_type?: string | null;
  professional_license?: string | null;
  email?: string | null;
  phone?: string | null;
  status?: string;
};
export type CreatePractitionerPayload = Required<Pick<UpsertPractitionerPayload, 'full_name'>> & Omit<UpsertPractitionerPayload, 'full_name' | 'status'>;

export const adminResourcesApi = {
  listOrganizations: (tenantId: string) => apiRequest<Organization[]>('/api/admin/organizations', { tenantId }),
  createOrganization: (tenantId: string, payload: CreateOrganizationPayload) => apiRequest<Organization>('/api/admin/organizations', { tenantId, method: 'POST', body: JSON.stringify(payload) }),
  updateOrganization: (tenantId: string, organizationId: string, payload: UpsertOrganizationPayload) => apiRequest<Organization>(`/api/admin/organizations/${organizationId}`, { tenantId, method: 'PATCH', body: JSON.stringify(payload) }),
  disableOrganization: (tenantId: string, organizationId: string) => apiRequest<Organization>(`/api/admin/organizations/${organizationId}/disable`, { tenantId, method: 'POST', body: JSON.stringify({}) }),
  activateOrganization: (tenantId: string, organizationId: string) => adminResourcesApi.updateOrganization(tenantId, organizationId, { status: 'active' }),

  listLocations: (tenantId: string) => apiRequest<Location[]>('/api/admin/locations', { tenantId }),
  createLocation: (tenantId: string, payload: CreateLocationPayload) => apiRequest<Location>('/api/admin/locations', { tenantId, method: 'POST', body: JSON.stringify(payload) }),
  updateLocation: (tenantId: string, locationId: string, payload: UpsertLocationPayload) => apiRequest<Location>(`/api/admin/locations/${locationId}`, { tenantId, method: 'PATCH', body: JSON.stringify(payload) }),
  disableLocation: (tenantId: string, locationId: string) => apiRequest<Location>(`/api/admin/locations/${locationId}/disable`, { tenantId, method: 'POST', body: JSON.stringify({}) }),
  activateLocation: (tenantId: string, locationId: string) => adminResourcesApi.updateLocation(tenantId, locationId, { status: 'active' }),

  listRooms: (tenantId: string) => apiRequest<Room[]>('/api/admin/rooms', { tenantId }),
  createRoom: (tenantId: string, payload: CreateRoomPayload) => apiRequest<Room>('/api/admin/rooms', { tenantId, method: 'POST', body: JSON.stringify(payload) }),
  updateRoom: (tenantId: string, roomId: string, payload: UpsertRoomPayload) => apiRequest<Room>(`/api/admin/rooms/${roomId}`, { tenantId, method: 'PATCH', body: JSON.stringify(payload) }),
  disableRoom: (tenantId: string, roomId: string) => apiRequest<Room>(`/api/admin/rooms/${roomId}/disable`, { tenantId, method: 'POST', body: JSON.stringify({}) }),
  activateRoom: (tenantId: string, roomId: string) => adminResourcesApi.updateRoom(tenantId, roomId, { status: 'active' }),

  listPractitioners: (tenantId: string) => apiRequest<Practitioner[]>('/api/admin/practitioners', { tenantId }),
  createPractitioner: (tenantId: string, payload: CreatePractitionerPayload) => apiRequest<Practitioner>('/api/admin/practitioners', { tenantId, method: 'POST', body: JSON.stringify(payload) }),
  updatePractitioner: (tenantId: string, practitionerId: string, payload: UpsertPractitionerPayload) => apiRequest<Practitioner>(`/api/admin/practitioners/${practitionerId}`, { tenantId, method: 'PATCH', body: JSON.stringify(payload) }),
  disablePractitioner: (tenantId: string, practitionerId: string) => adminResourcesApi.updatePractitioner(tenantId, practitionerId, { status: 'inactive' }),
  activatePractitioner: (tenantId: string, practitionerId: string) => adminResourcesApi.updatePractitioner(tenantId, practitionerId, { status: 'active' }),
};
