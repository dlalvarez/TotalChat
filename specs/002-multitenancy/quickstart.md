# Quickstart — Spec 002 Multi-Tenancy

## Crear tenant demo

```bash
curl -X POST http://localhost:8000/api/platform/tenants \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Consultorio Psicóloga Ana",
    "slug": "psicologa-ana",
    "owner_email": "ana@example.com",
    "owner_full_name": "Ana Gómez",
    "provision_schema": true
  }'
```

## Validaciones

1. Existe registro en `public.tenants`.
2. Existe schema del tenant.
3. Las migraciones base se aplicaron al schema.
4. Crear dos tenants no mezcla datos.
5. Usuario solo accede a tenants asignados.

## Run public migrations locally

The Alembic baseline lives under `backend/alembic`. Configure `TOTALCHAT_DATABASE_URL`
for a PostgreSQL database, then run:

```bash
cd backend
alembic upgrade head
```

Tenant provisioning creates a sanitized tenant schema and initializes tenant schema
migration tracking only. Booking-domain tables are intentionally excluded from this phase.
