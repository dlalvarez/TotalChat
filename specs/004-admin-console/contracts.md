# Contracts — 004-admin-console

Pendiente de definir endpoints/API contracts durante el plan técnico.

## Fase 6B.5 — Relación organización-profesional

- `GET /api/admin/organization-practitioners`
- `POST /api/admin/organization-practitioners`
- `PATCH /api/admin/organizations/{organization_id}/practitioners/{practitioner_id}`
- `POST /api/admin/organizations/{organization_id}/practitioners/{practitioner_id}/disable`

Las respuestas incluyen nombres legibles de organización/profesional y no exponen `schema_name`.


## Fase 6B.6 — Practitioner services

Endpoints funcionales: `GET /api/admin/practitioner-services`, `POST /api/admin/practitioner-services`, `GET /api/admin/practitioner-services/{service_id}`, `PATCH /api/admin/practitioner-services/{service_id}`, `POST /api/admin/practitioner-services/{service_id}/disable`. La respuesta incluye `organization_name`, `organization_status`, `practitioner_name`, `practitioner_status` y `organization_practitioner_status`.

Crear o reactivar requiere padres activos y relación `organization_practitioners` activa. No se aceptan campos extra ni `schema_name`.
