# Data Model — Spec 002 Multi-Tenancy

## public.tenants

```text
id
name
slug
schema_name
status
plan_id nullable
created_at
updated_at
```

## public.tenant_channels

```text
id
tenant_id
channel_type
external_identifier
webhook_secret_hash nullable
settings
is_active
created_at
updated_at
```

## public.users

```text
id
email
password_hash
full_name
status
created_at
updated_at
```

## public.user_tenants

```text
user_id
tenant_id
role
status
created_at
updated_at
```

## Reglas

- `slug` único.
- `schema_name` único.
- `schema_name` derivado y sanitizado.
- No usar schema sin registro tenant activo.
