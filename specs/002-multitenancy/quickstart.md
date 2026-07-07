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
