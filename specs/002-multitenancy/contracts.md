# Contracts — Spec 002 Multi-Tenancy

## Endpoints

### POST /api/platform/tenants

Request:

```json
{
  "name": "Consultorio Psicóloga Ana",
  "slug": "psicologa-ana",
  "owner_email": "ana@example.com",
  "owner_full_name": "Ana Gómez",
  "provision_schema": true
}
```

Response:

```json
{
  "data": {
    "id": "uuid",
    "name": "Consultorio Psicóloga Ana",
    "slug": "psicologa-ana",
    "status": "active",
    "schema_status": "provisioned"
  }
}
```

### GET /api/platform/tenants

Lista tenants.

### POST /api/platform/tenants/{tenant_id}/channels

Request Telegram:

```json
{
  "channel_type": "telegram",
  "external_identifier": "totalchat_demo_bot",
  "settings": {
    "webhook_enabled": true
  }
}
```

## Reglas

- El backend genera `schema_name`.
- No exponer `schema_name` al frontend de forma innecesaria.
- El LLM no participa en resolver tenants.
- Toda operación admin futura debe tener contexto tenant validado.
- Deben existir tests de aislamiento.

## Errores

- `TENANT_NOT_FOUND`
- `VALIDATION_ERROR`
- `CONFLICT`
- `AUTHORIZATION_FAILED`
