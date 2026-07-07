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
