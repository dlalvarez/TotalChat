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
