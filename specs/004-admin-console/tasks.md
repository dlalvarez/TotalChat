# Tasks 004 — Admin Console

- [x] Crear app frontend.
- [x] Crear login.
  - Fase 6C.2 implementa login real con `POST /api/auth/login`, `GET /api/auth/me`, JWT access token de 30 minutos usando `TOTALCHAT_JWT_SECRET` y autorización admin por token + `X-TotalChat-Tenant-Id`.
  - `POST /api/auth/refresh`, gestión UI de usuarios, invitaciones y self-service signup quedan diferidos explícitamente.
- [x] Crear layout.
- [x] Crear dashboard.
  - Fase 6D.1 reemplaza datos demo por `GET /api/admin/dashboard/summary` tenant-scoped con métricas reales, agenda de hoy, pagos pendientes de revisión y alertas de links virtuales sin exponer `schema_name`.
- [x] CRUD organizaciones.
- [x] CRUD sedes.
- [x] CRUD consultorios.
- [x] CRUD profesionales.
- [x] CRUD especialidades.
- [x] Relación organización-profesional.
- [x] CRUD servicios.
  - Depende de `organization_practitioners` activa.
  - No incluye precios, modalidades ni disponibilidad.
- [x] CRUD pagadores y planes.
  - Administra `payer_types`, `payers` y `payer_plans`.
  - No incluye precios ni tarifas.
- [x] CRUD tarifas.
  - Administra precios por servicio del profesional y plan de pagador.
  - Usa COP como moneda operativa temporal en consola; no incluye multi-moneda, pagos, citas ni disponibilidad.
- [x] Pantalla disponibilidad.
  - Reglas recurrentes de atención.
  - Bloqueos e indisponibilidad administrativos.
- [x] Pantalla citas.
- [x] Pantalla pacientes.
  - Gestiona pacientes administrativos básicos: listar, detalle, crear, editar, inactivar y reactivar sin borrado físico.
  - No incluye historia clínica, datos clínicos, fusión/deduplicación avanzada, contactos múltiples ni perfiles de pagador automáticos.
- [x] Pantalla pagos.
  - Implementación base cerrada y validada post-merge en PR #44.
- [x] Links virtuales manuales integrados en pantalla Citas.
  - No existe pantalla independiente de links virtuales en este MVP.

## Fase 6B.13 — Citas virtuales con link manual

- [x] Derivar modalidad de cita administrativa desde `locations.is_virtual`.
- [x] Quitar modalidad como campo editable del frontend/payload.
- [x] Mantener datos de link virtual manual como columnas de `bookings`.
- [x] Mostrar UI diferenciada para cita virtual/presencial según sede.
- [x] Rechazar consultorio en sedes virtuales y datos virtuales en sedes presenciales.


## Fase 6C.1 — Bootstrap de usuario owner administrativo

- [x] Crear servicio backend interno para bootstrap de usuario admin en `public.users` y `public.user_tenants`.
- [x] Crear comando CLI `python3 -m app.auth.create_admin_user` con password por prompt seguro o `TOTALCHAT_BOOTSTRAP_ADMIN_PASSWORD`.
- [x] Mantener fuera de alcance login UI, endpoint de login, JWT, refresh tokens, gestión de usuarios e invitaciones.


## Fase 6C.1.1 — CLI operativo idempotente de provisioning de tenant

- [x] Crear comando CLI `python3 -m app.tenancy.create_tenant` con argumentos `--name` y `--slug`.
- [x] Mantener `schema_name` generado internamente desde slug, sin aceptarlo ni mostrarlo en la salida principal.
- [x] Hacer idempotente la creación de `public.tenants`, schema tenant y migraciones base/booking.
- [x] Rechazar tenants existentes inactivos sin reactivarlos automáticamente.
- [x] Documentar el procedimiento operativo `tc-dev-01` y el encadenamiento con `app.auth.create_admin_user`.
- [x] Mantener fuera de alcance login UI, `/api/auth/login`, JWT, refresh tokens, gestión SaaS de tenants, self-service signup y creación automática de owner.
