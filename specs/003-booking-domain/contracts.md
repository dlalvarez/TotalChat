# Contracts — Spec 003 Booking Domain Core

Este documento usa `docs/API_CONTRACTS.md` como fuente principal.

## Endpoints mínimos de dominio

### Organizaciones

- POST `/api/admin/organizations`
- GET `/api/admin/organizations`
- GET `/api/admin/organizations/{organization_id}`
- PATCH `/api/admin/organizations/{organization_id}`
- POST `/api/admin/organizations/{organization_id}/disable`

### Sedes y consultorios

- POST `/api/admin/locations`
- GET `/api/admin/locations`
- POST `/api/admin/rooms`
- GET `/api/admin/rooms`

### Profesionales

- POST `/api/admin/practitioners`
- GET `/api/admin/practitioners`
- PATCH `/api/admin/practitioners/{practitioner_id}`

### Especialidades

- POST `/api/admin/specialties`
- GET `/api/admin/specialties`

### Servicios

- POST `/api/admin/practitioner-services`
- GET `/api/admin/practitioner-services`
- POST `/api/admin/practitioner-services/{service_id}/modalities`

### Precios

- POST `/api/admin/payer-types`
- POST `/api/admin/payers`
- POST `/api/admin/payer-plans`
- POST `/api/admin/practitioner-service-prices`
- GET `/api/admin/practitioner-services/{service_id}/prices`

### Pacientes

- POST `/api/admin/patients`
- POST `/api/admin/patients/{patient_id}/payer-profiles`

### Disponibilidad

- POST `/api/admin/availability-rules`
- POST `/api/admin/availability-exceptions`
- GET `/api/admin/availability/slots`

### Citas

- POST `/api/admin/bookings`
- POST `/api/admin/bookings/{booking_id}/confirm`
- POST `/api/admin/bookings/{booking_id}/cancel`
- POST `/api/admin/bookings/{booking_id}/reschedule`

## Reglas

- Seguir `docs/API_CONTRACTS.md`.
- Estados deben seguir `docs/STATE_MACHINES.md`.
- Disponibilidad debe pasar por `SchedulingProvider`.
- Citas deben guardar snapshot.
- Paciente mínimo debe ser válido.
- Precio desconocido no debe inventarse.
