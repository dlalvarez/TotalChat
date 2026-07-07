# Data Model — Spec 000B

## public.solutions

```text
id
code
name
description
status
created_at
updated_at
```

Registros iniciales:

```text
medichat
restochat
hotelchat
staychat
storechat
```

## public.tenant_solutions

```text
id
tenant_id
solution_id
status
settings
created_at
updated_at
```

Para MVP se usará `medichat`.
