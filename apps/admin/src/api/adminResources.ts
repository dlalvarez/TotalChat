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

export const ROOM_TYPE_OPTIONS = [
  { value: 'consulta_general', label: 'Consulta general' },
  { value: 'procedimientos', label: 'Procedimientos' },
  { value: 'terapia', label: 'Terapia' },
  { value: 'diagnostico', label: 'Diagnóstico' },
  { value: 'virtual', label: 'Virtual' },
  { value: 'otro', label: 'Otro' },
] as const;
export type RoomType = (typeof ROOM_TYPE_OPTIONS)[number]['value'];
export const roomTypeLabel = (value: string | null | undefined) => ROOM_TYPE_OPTIONS.find((option) => option.value === value)?.label ?? value ?? 'Sin tipo';

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

export type Specialty = {
  id: string;
  name: string;
  description: string | null;
  status: string;
};

export type UpsertSpecialtyPayload = { name?: string; description?: string | null; status?: string };
export type CreateSpecialtyPayload = Required<Pick<UpsertSpecialtyPayload, 'name'>> & Omit<UpsertSpecialtyPayload, 'name' | 'status'>;

export type PractitionerSpecialty = {
  practitioner_id: string;
  specialty_id: string;
  specialty_name: string | null;
  specialty_status: string | null;
  status: string;
};


export const ORGANIZATION_PRACTITIONER_ROLE_OPTIONS = [
  { value: 'primary', label: 'Principal' },
  { value: 'member', label: 'Miembro' },
  { value: 'external', label: 'Externo' },
] as const;
export const organizationPractitionerRoleLabel = (value: string) => ORGANIZATION_PRACTITIONER_ROLE_OPTIONS.find((option) => option.value === value)?.label ?? value;

export type OrganizationPractitioner = {
  organization_id: string;
  organization_name: string | null;
  organization_status: string | null;
  practitioner_id: string;
  practitioner_name: string | null;
  practitioner_status: string | null;
  role: string;
  status: string;
};

export type UpsertOrganizationPractitionerPayload = { role?: string; status?: string };
export type CreateOrganizationPractitionerPayload = { organization_id: string; practitioner_id: string; role?: string };


export type PractitionerService = {
  id: string;
  organization_id: string;
  organization_name: string | null;
  organization_status: string | null;
  practitioner_id: string;
  practitioner_name: string | null;
  practitioner_status: string | null;
  organization_practitioner_status: string | null;
  name: string;
  description: string | null;
  duration_minutes: number;
  requires_payment: boolean;
  status: string;
};
export type UpsertPractitionerServicePayload = { name?: string; description?: string | null; duration_minutes?: number; requires_payment?: boolean; status?: string };
export type CreatePractitionerServicePayload = { organization_id: string; practitioner_id: string; name: string; description?: string | null; duration_minutes: number; requires_payment?: boolean };


export type PayerType = { id: string; code: string; name: string; description: string | null; status: string };
export type UpsertPayerTypePayload = { code?: string; name?: string; description?: string | null; status?: string };
export type CreatePayerTypePayload = { code: string; name: string; description?: string | null };
export type Payer = { id: string; payer_type_id: string; payer_type_name: string | null; payer_type_code: string | null; payer_type_status: string | null; name: string; description: string | null; status: string };
export type UpsertPayerPayload = { name?: string; description?: string | null; status?: string };
export type CreatePayerPayload = { payer_type_id: string; name: string; description?: string | null };
export type PayerPlan = { id: string; payer_id: string; payer_name: string | null; payer_status: string | null; payer_type_id: string | null; payer_type_name: string | null; payer_type_code: string | null; payer_type_status: string | null; name: string; description: string | null; status: string };
export type UpsertPayerPlanPayload = { name?: string; description?: string | null; status?: string };
export type CreatePayerPlanPayload = { payer_id: string; name: string; description?: string | null };


export type PractitionerServicePrice = {
  id: string;
  practitioner_service_id: string;
  practitioner_service_name: string | null;
  practitioner_service_status: string | null;
  organization_id: string | null;
  organization_name: string | null;
  organization_status: string | null;
  practitioner_id: string | null;
  practitioner_name: string | null;
  practitioner_status: string | null;
  payer_plan_id: string;
  payer_plan_name: string | null;
  payer_plan_status: string | null;
  payer_id: string | null;
  payer_name: string | null;
  payer_status: string | null;
  payer_type_id: string | null;
  payer_type_name: string | null;
  payer_type_code: string | null;
  payer_type_status: string | null;
  price: number;
  currency: string;
  valid_from: string;
  valid_to: string | null;
  status: string;
};
export const AVAILABILITY_EXCEPTION_TYPE_OPTIONS = [
  { value: 'vacation', label: 'Vacaciones' },
  { value: 'medical_leave', label: 'Incapacidad' },
  { value: 'personal', label: 'Espacio personal' },
  { value: 'meeting', label: 'Reunión' },
  { value: 'lunch', label: 'Almuerzo' },
  { value: 'training', label: 'Capacitación' },
  { value: 'maintenance', label: 'Mantenimiento' },
  { value: 'temporary_closure', label: 'Cierre temporal' },
  { value: 'administrative', label: 'Bloqueo administrativo' },
  { value: 'other', label: 'Otro' },
] as const;
export type AvailabilityException = { id: string; practitioner_id: string; practitioner_name: string | null; practitioner_status: string | null; location_id: string | null; location_name: string | null; location_status: string | null; organization_id: string | null; organization_name: string | null; organization_status: string | null; room_id: string | null; room_name: string | null; room_status: string | null; starts_at: string; ends_at: string; exception_type: string; exception_type_label: string; reason: string | null; status: string };
export type CreateAvailabilityExceptionPayload = { practitioner_id: string; location_id?: string | null; room_id?: string | null; starts_at: string; ends_at: string; exception_type: string; reason?: string | null };
export type UpsertAvailabilityExceptionPayload = { starts_at?: string; ends_at?: string; exception_type?: string; reason?: string | null; status?: string };

export type PractitionerAvailabilityRule = { id: string; organization_id: string; organization_name: string | null; organization_status: string | null; practitioner_id: string; practitioner_name: string | null; practitioner_status: string | null; organization_practitioner_status: string | null; practitioner_service_id: string | null; practitioner_service_name: string | null; practitioner_service_status: string | null; scope_label: string; day_of_week: number; start_time: string; end_time: string; valid_from: string; valid_to: string | null; status: string };
export type CreatePractitionerAvailabilityRulePayload = { organization_id: string; practitioner_id: string; practitioner_service_id?: string | null; day_of_week: number; start_time: string; end_time: string; valid_from: string; valid_to?: string | null };
export type UpsertPractitionerAvailabilityRulePayload = { day_of_week?: number; start_time?: string; end_time?: string; valid_from?: string; valid_to?: string | null; status?: string };

export type CreatePractitionerServicePricePayload = { practitioner_service_id: string; payer_plan_id: string; price: number; currency: 'COP'; valid_from: string; valid_to?: string | null };
export type UpsertPractitionerServicePricePayload = { price?: number; currency?: string; valid_from?: string; valid_to?: string | null; status?: string };

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


  listOrganizationPractitioners: (tenantId: string) => apiRequest<OrganizationPractitioner[]>('/api/admin/organization-practitioners', { tenantId }),
  createOrganizationPractitioner: (tenantId: string, payload: CreateOrganizationPractitionerPayload) => apiRequest<OrganizationPractitioner>('/api/admin/organization-practitioners', { tenantId, method: 'POST', body: JSON.stringify(payload) }),
  updateOrganizationPractitioner: (tenantId: string, organizationId: string, practitionerId: string, payload: UpsertOrganizationPractitionerPayload) => apiRequest<OrganizationPractitioner>(`/api/admin/organizations/${organizationId}/practitioners/${practitionerId}`, { tenantId, method: 'PATCH', body: JSON.stringify(payload) }),
  disableOrganizationPractitioner: (tenantId: string, organizationId: string, practitionerId: string) => apiRequest<OrganizationPractitioner>(`/api/admin/organizations/${organizationId}/practitioners/${practitionerId}/disable`, { tenantId, method: 'POST', body: JSON.stringify({}) }),
  activateOrganizationPractitioner: (tenantId: string, organizationId: string, practitionerId: string) => adminResourcesApi.updateOrganizationPractitioner(tenantId, organizationId, practitionerId, { status: 'active' }),

  listPayerTypes: (tenantId: string) => apiRequest<PayerType[]>('/api/admin/payer-types', { tenantId }),
  createPayerType: (tenantId: string, payload: CreatePayerTypePayload) => apiRequest<PayerType>('/api/admin/payer-types', { tenantId, method: 'POST', body: JSON.stringify(payload) }),
  updatePayerType: (tenantId: string, payerTypeId: string, payload: UpsertPayerTypePayload) => apiRequest<PayerType>(`/api/admin/payer-types/${payerTypeId}`, { tenantId, method: 'PATCH', body: JSON.stringify(payload) }),
  disablePayerType: (tenantId: string, payerTypeId: string) => apiRequest<PayerType>(`/api/admin/payer-types/${payerTypeId}/disable`, { tenantId, method: 'POST', body: JSON.stringify({}) }),
  activatePayerType: (tenantId: string, payerTypeId: string) => adminResourcesApi.updatePayerType(tenantId, payerTypeId, { status: 'active' }),

  listPayers: (tenantId: string) => apiRequest<Payer[]>('/api/admin/payers', { tenantId }),
  createPayer: (tenantId: string, payload: CreatePayerPayload) => apiRequest<Payer>('/api/admin/payers', { tenantId, method: 'POST', body: JSON.stringify(payload) }),
  updatePayer: (tenantId: string, payerId: string, payload: UpsertPayerPayload) => apiRequest<Payer>(`/api/admin/payers/${payerId}`, { tenantId, method: 'PATCH', body: JSON.stringify(payload) }),
  disablePayer: (tenantId: string, payerId: string) => apiRequest<Payer>(`/api/admin/payers/${payerId}/disable`, { tenantId, method: 'POST', body: JSON.stringify({}) }),
  activatePayer: (tenantId: string, payerId: string) => adminResourcesApi.updatePayer(tenantId, payerId, { status: 'active' }),

  listPayerPlans: (tenantId: string) => apiRequest<PayerPlan[]>('/api/admin/payer-plans', { tenantId }),
  createPayerPlan: (tenantId: string, payload: CreatePayerPlanPayload) => apiRequest<PayerPlan>('/api/admin/payer-plans', { tenantId, method: 'POST', body: JSON.stringify(payload) }),
  updatePayerPlan: (tenantId: string, payerPlanId: string, payload: UpsertPayerPlanPayload) => apiRequest<PayerPlan>(`/api/admin/payer-plans/${payerPlanId}`, { tenantId, method: 'PATCH', body: JSON.stringify(payload) }),
  disablePayerPlan: (tenantId: string, payerPlanId: string) => apiRequest<PayerPlan>(`/api/admin/payer-plans/${payerPlanId}/disable`, { tenantId, method: 'POST', body: JSON.stringify({}) }),
  activatePayerPlan: (tenantId: string, payerPlanId: string) => adminResourcesApi.updatePayerPlan(tenantId, payerPlanId, { status: 'active' }),

  listPractitionerServices: (tenantId: string) => apiRequest<PractitionerService[]>('/api/admin/practitioner-services', { tenantId }),
  createPractitionerService: (tenantId: string, payload: CreatePractitionerServicePayload) => apiRequest<PractitionerService>('/api/admin/practitioner-services', { tenantId, method: 'POST', body: JSON.stringify(payload) }),
  updatePractitionerService: (tenantId: string, serviceId: string, payload: UpsertPractitionerServicePayload) => apiRequest<PractitionerService>(`/api/admin/practitioner-services/${serviceId}`, { tenantId, method: 'PATCH', body: JSON.stringify(payload) }),
  disablePractitionerService: (tenantId: string, serviceId: string) => apiRequest<PractitionerService>(`/api/admin/practitioner-services/${serviceId}/disable`, { tenantId, method: 'POST', body: JSON.stringify({}) }),
  activatePractitionerService: (tenantId: string, serviceId: string) => adminResourcesApi.updatePractitionerService(tenantId, serviceId, { status: 'active' }),

  listAvailabilityExceptions: (tenantId: string) => apiRequest<AvailabilityException[]>('/api/admin/availability-exceptions', { tenantId }),
  createAvailabilityException: (tenantId: string, payload: CreateAvailabilityExceptionPayload) => apiRequest<AvailabilityException>('/api/admin/availability-exceptions', { tenantId, method: 'POST', body: JSON.stringify(payload) }),
  updateAvailabilityException: (tenantId: string, exceptionId: string, payload: UpsertAvailabilityExceptionPayload) => apiRequest<AvailabilityException>(`/api/admin/availability-exceptions/${exceptionId}`, { tenantId, method: 'PATCH', body: JSON.stringify(payload) }),
  disableAvailabilityException: (tenantId: string, exceptionId: string) => apiRequest<AvailabilityException>(`/api/admin/availability-exceptions/${exceptionId}/disable`, { tenantId, method: 'POST', body: JSON.stringify({}) }),
  activateAvailabilityException: (tenantId: string, exceptionId: string) => adminResourcesApi.updateAvailabilityException(tenantId, exceptionId, { status: 'active' }),

  listPractitionerAvailabilityRules: (tenantId: string) => apiRequest<PractitionerAvailabilityRule[]>('/api/admin/practitioner-availability-rules', { tenantId }),
  createPractitionerAvailabilityRule: (tenantId: string, payload: CreatePractitionerAvailabilityRulePayload) => apiRequest<PractitionerAvailabilityRule>('/api/admin/practitioner-availability-rules', { tenantId, method: 'POST', body: JSON.stringify(payload) }),
  updatePractitionerAvailabilityRule: (tenantId: string, ruleId: string, payload: UpsertPractitionerAvailabilityRulePayload) => apiRequest<PractitionerAvailabilityRule>(`/api/admin/practitioner-availability-rules/${ruleId}`, { tenantId, method: 'PATCH', body: JSON.stringify(payload) }),
  disablePractitionerAvailabilityRule: (tenantId: string, ruleId: string) => apiRequest<PractitionerAvailabilityRule>(`/api/admin/practitioner-availability-rules/${ruleId}/disable`, { tenantId, method: 'POST', body: JSON.stringify({}) }),
  activatePractitionerAvailabilityRule: (tenantId: string, ruleId: string) => adminResourcesApi.updatePractitionerAvailabilityRule(tenantId, ruleId, { status: 'active' }),

  listPractitionerServicePrices: (tenantId: string) => apiRequest<PractitionerServicePrice[]>('/api/admin/practitioner-service-prices', { tenantId }),
  createPractitionerServicePrice: (tenantId: string, payload: CreatePractitionerServicePricePayload) => apiRequest<PractitionerServicePrice>('/api/admin/practitioner-service-prices', { tenantId, method: 'POST', body: JSON.stringify(payload) }),
  updatePractitionerServicePrice: (tenantId: string, priceId: string, payload: UpsertPractitionerServicePricePayload) => apiRequest<PractitionerServicePrice>(`/api/admin/practitioner-service-prices/${priceId}`, { tenantId, method: 'PATCH', body: JSON.stringify(payload) }),
  disablePractitionerServicePrice: (tenantId: string, priceId: string) => apiRequest<PractitionerServicePrice>(`/api/admin/practitioner-service-prices/${priceId}/disable`, { tenantId, method: 'POST', body: JSON.stringify({}) }),
  activatePractitionerServicePrice: (tenantId: string, priceId: string) => adminResourcesApi.updatePractitionerServicePrice(tenantId, priceId, { status: 'active' }),

  listPractitioners: (tenantId: string) => apiRequest<Practitioner[]>('/api/admin/practitioners', { tenantId }),
  createPractitioner: (tenantId: string, payload: CreatePractitionerPayload) => apiRequest<Practitioner>('/api/admin/practitioners', { tenantId, method: 'POST', body: JSON.stringify(payload) }),
  updatePractitioner: (tenantId: string, practitionerId: string, payload: UpsertPractitionerPayload) => apiRequest<Practitioner>(`/api/admin/practitioners/${practitionerId}`, { tenantId, method: 'PATCH', body: JSON.stringify(payload) }),
  disablePractitioner: (tenantId: string, practitionerId: string) => adminResourcesApi.updatePractitioner(tenantId, practitionerId, { status: 'inactive' }),
  activatePractitioner: (tenantId: string, practitionerId: string) => adminResourcesApi.updatePractitioner(tenantId, practitionerId, { status: 'active' }),

  listSpecialties: (tenantId: string) => apiRequest<Specialty[]>('/api/admin/specialties', { tenantId }),
  createSpecialty: (tenantId: string, payload: CreateSpecialtyPayload) => apiRequest<Specialty>('/api/admin/specialties', { tenantId, method: 'POST', body: JSON.stringify(payload) }),
  updateSpecialty: (tenantId: string, specialtyId: string, payload: UpsertSpecialtyPayload) => apiRequest<Specialty>(`/api/admin/specialties/${specialtyId}`, { tenantId, method: 'PATCH', body: JSON.stringify(payload) }),
  disableSpecialty: (tenantId: string, specialtyId: string) => apiRequest<Specialty>(`/api/admin/specialties/${specialtyId}/disable`, { tenantId, method: 'POST', body: JSON.stringify({}) }),
  activateSpecialty: (tenantId: string, specialtyId: string) => adminResourcesApi.updateSpecialty(tenantId, specialtyId, { status: 'active' }),

  listPractitionerSpecialties: (tenantId: string, practitionerId: string) => apiRequest<PractitionerSpecialty[]>(`/api/admin/practitioners/${practitionerId}/specialties`, { tenantId }),
  syncPractitionerSpecialties: (tenantId: string, practitionerId: string, specialtyIds: string[]) => apiRequest<PractitionerSpecialty[]>(`/api/admin/practitioners/${practitionerId}/specialties`, { tenantId, method: 'PUT', body: JSON.stringify({ specialty_ids: specialtyIds }) }),
  assignPractitionerSpecialty: (tenantId: string, practitionerId: string, specialtyId: string) => apiRequest<PractitionerSpecialty>(`/api/admin/practitioners/${practitionerId}/specialties`, { tenantId, method: 'POST', body: JSON.stringify({ specialty_id: specialtyId }) }),
  disablePractitionerSpecialty: (tenantId: string, practitionerId: string, specialtyId: string) => apiRequest<PractitionerSpecialty>(`/api/admin/practitioners/${practitionerId}/specialties/${specialtyId}/disable`, { tenantId, method: 'POST', body: JSON.stringify({}) }),
};
