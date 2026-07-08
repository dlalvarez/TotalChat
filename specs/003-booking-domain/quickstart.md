# Quickstart — Spec 003 Booking Domain Core

## Objetivo

Crear datos mínimos para reservar una cita interna.

## Secuencia

1. Crear organización.
2. Crear sede.
3. Crear consultorio.
4. Crear profesional.
5. Crear especialidad.
6. Asociar profesional a especialidad.
7. Crear servicio del profesional.
8. Crear modalidad.
9. Crear payer_type Particular.
10. Crear payer Particular.
11. Crear payer_plan Tarifa particular.
12. Crear precio del servicio.
13. Crear disponibilidad.
14. Consultar slots.
15. Crear paciente mínimo.
16. Crear booking.
17. Validar snapshot.

## Resultado esperado

```text
booking.status = tentative or pending_payment
booking.service_name_snapshot is not null
booking.price_snapshot is not null
booking.payer_plan_name_snapshot is not null
patient.profile_status = minimal or incomplete
```

## Fixture recomendado

Usar `docs/TEST_FIXTURES.md`, tenant demo `Consultorio Psicóloga Ana`.

## Migración tenant

La línea base de tablas del dominio de reservas se aplica por schema de tenant después de `002_base` mediante `apply_booking_domain_tenant_migration(connection, schema_name)`. Esta migración registra la versión `003_booking_domain` en `<tenant_schema>.tenant_schema_migrations` y no crea tablas del dominio de reservas en `public`.

## Servicios internos de reserva

La creación programática de una reserva tentativa debe ejecutarse desde servicios internos del backend, sin exponer endpoints en esta fase:

1. Resolver el tenant mediante infraestructura confiable y construir `TenantContext`.
2. Abrir una `sqlalchemy.orm.Session` apuntando al schema operativo del tenant.
3. Llamar `BookingService.create_tentative_booking(...)` con `practitioner_service_id`, `payer_plan_id`, horario, modalidad y paciente mínimo o `patient_id`.
4. `PricingService` resuelve tarifa solo por `practitioner_service + payer_plan` vigente; la especialidad no participa en precio.
5. `BookingSnapshotBuilder` guarda la verdad histórica de servicio, profesional, modalidad, sede, plan, precio, moneda, total, dirección y consultorio donde aplique.
6. Las transiciones posteriores de booking deben pasar por `BookingTransitionService` y respetar `docs/STATE_MACHINES.md`.

Exclusiones de esta fase: routers FastAPI, pagos, adaptadores externos de agenda/calendario, Telegram, LangGraph y consola administrativa.

## Internal scheduling provider baseline

The MVP internal scheduling provider remains a backend-only service baseline; it does not expose admin API endpoints in this phase. Slot lookup requires an explicit trusted `TenantContext` and never accepts `schema_name` from client input.

Availability slot generation uses tenant-scoped `availability_rules` with ISO weekday numbering (Monday=1, Sunday=7), the selected `practitioner_service.duration_minutes`, practitioner, modality, location, and room constraints. A rule with `practitioner_service_id = null` can apply to compatible services. Active `availability_exceptions` and active/protected bookings block overlapping slots; terminal bookings do not block availability. Returned internal slots include start/end times, practitioner, location, room, modality, and `source = "internal"`.

## Admin availability slots API baseline

PR #7 exposes `GET /api/admin/availability/slots` for admin slot lookup only. The endpoint requires `X-TotalChat-Tenant-Id` with an active tenant UUID, resolves the tenant from `public.tenants`, and does not accept or return `schema_name`. Full admin user-to-tenant authorization remains a future auth/admin phase.

Supported query parameters are `practitioner_service_id`, optional `practitioner_id`, `modality`, `date_from`, `date_to`, optional `payer_plan_id`, optional `location_id`, and optional `room_id`. `payer_plan_id` is accepted for contract compatibility, but pricing logic is not part of slot lookup. The route delegates slot calculation to the `SchedulingProvider` baseline (`InternalSchedulingProvider`) and returns successful responses as `{"data": [...]}`.
