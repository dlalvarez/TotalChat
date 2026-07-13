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

## Fase 6B.7 — Pagadores y planes

Endpoints funcionales: `GET /api/admin/payer-types`, `GET /api/admin/payer-types/{payer_type_id}`, `POST /api/admin/payer-types`, `PATCH /api/admin/payer-types/{payer_type_id}`, `POST /api/admin/payer-types/{payer_type_id}/disable`; `GET /api/admin/payers`, `GET /api/admin/payers/{payer_id}`, `POST /api/admin/payers`, `PATCH /api/admin/payers/{payer_id}`, `POST /api/admin/payers/{payer_id}/disable`; `GET /api/admin/payer-plans`, `GET /api/admin/payer-plans/{payer_plan_id}`, `POST /api/admin/payer-plans`, `PATCH /api/admin/payer-plans/{payer_plan_id}`, `POST /api/admin/payer-plans/{payer_plan_id}/disable`.

`PATCH` reactiva con `status: active`. Las respuestas de pagadores incluyen `payer_type_name`, `payer_type_code` y `payer_type_status`; las respuestas de planes incluyen `payer_name`, `payer_status`, `payer_type_id`, `payer_type_name`, `payer_type_code` y `payer_type_status`. No se acepta `schema_name` ni campos extra.

## Fase 6B.8 — Precios / tarifas

Endpoints funcionales: `GET /api/admin/practitioner-service-prices`, `GET /api/admin/practitioner-service-prices/{price_id}`, `POST /api/admin/practitioner-service-prices`, `PATCH /api/admin/practitioner-service-prices/{price_id}`, `POST /api/admin/practitioner-service-prices/{price_id}/disable` y compatibilidad con `GET /api/admin/practitioner-services/{service_id}/prices`.

Las respuestas incluyen nombres legibles y estados de servicio, organización, profesional, plan, pagador y tipo de pagador. Crear/reactivar exige padres activos. La API valida monto no negativo, moneda ISO mayúscula de 3 letras, vigencias coherentes, unicidad por servicio + plan + `valid_from` y ausencia de solapamientos entre precios activos. No se expone `schema_name`.

## Fase 6B.9 — Disponibilidad base

Endpoints funcionales: `GET /api/admin/practitioner-availability-rules`, `GET /api/admin/practitioner-availability-rules/{rule_id}`, `POST /api/admin/practitioner-availability-rules`, `PATCH /api/admin/practitioner-availability-rules/{rule_id}` y `POST /api/admin/practitioner-availability-rules/{rule_id}/disable`.

La convención de `day_of_week` para esta pantalla es estable: `0 = Monday/Lunes` y `6 = Sunday/Domingo`. Las respuestas incluyen nombres y estados legibles de organización, profesional, servicio opcional y relación organización-profesional. Si `practitioner_service_id` es `null`, `scope_label` es `Todos los servicios`. El listado conserva por defecto reglas activas e inactivas para trazabilidad, con `include_inactive=false` disponible para filtrar activas. No se expone `schema_name`.

### Fase 6B.9.1 — Bloqueos e indisponibilidad

La disponibilidad base define elegibilidad de atención. Los bloqueos/indisponibilidades reducen esa elegibilidad para rangos futuros donde un profesional no puede atender, aunque sus reglas recurrentes indiquen que normalmente podría hacerlo. Las reservas, citas y holds serán los registros que ocupen realmente un horario en fases posteriores; esta fase no calcula slots, no crea citas y no crea reservas.

La consola administra bloqueos con profesional, sede opcional, consultorio opcional, inicio, fin, tipo controlado por backend, motivo opcional y estado activo/inactivo. No hay borrado físico. Los tipos de bloqueo del MVP son controlados para preservar semántica operativa y facilitar reglas futuras; la configuración dinámica por tenant queda como mejora futura.

## Fase 6B.10 — Citas administrativas

Endpoints funcionales: `GET /api/admin/appointments`, `GET /api/admin/appointments/{appointment_id}`, `POST /api/admin/appointments`, `PATCH /api/admin/appointments/{appointment_id}`, `POST /api/admin/appointments/{appointment_id}/cancel`, `POST /api/admin/appointments/{appointment_id}/complete` y `POST /api/admin/appointments/{appointment_id}/no-show`.

El listado acepta filtros por organización, sede, consultorio, profesional, servicio, paciente, estado y fecha/rango de fechas. `date_to` es inclusivo a fin de día. La respuesta serializa nombres legibles y labels de estado; no expone `schema_name`.

`PATCH` queda limitado a `notes` y `status` en esta fase para evitar edición estructural sin reprogramación visual. Cambios de fecha/hora quedan como fase futura explícita.

### Ajuste PR #43 — PATCH de citas y migración tenant

`PATCH /api/admin/appointments/{appointment_id}` permite `notes` siempre y permite `starts_at`, `ends_at` y `room_id` solo para citas `scheduled`. La reprogramación revalida rangos, consultorio activo en la misma sede, bloqueos activos aplicables, cita `scheduled` del mismo profesional y cita `scheduled` del mismo consultorio, excluyendo la cita editada. `status` sigue fuera del contrato PATCH.

Los tenants existentes reciben `bookings.notes` mediante el comando bajo demanda `python3 -m app.tenancy.migrate_existing_tenants`; no se requiere SQL manual.

## Fase 6B.11 — Pagos administrativos base

Endpoints funcionales: `GET /api/admin/payments`, `GET /api/admin/payments/{payment_attempt_id}`, `POST /api/admin/payments/{payment_attempt_id}/approve` y `POST /api/admin/payments/{payment_attempt_id}/reject`.

`GET /api/admin/payments` acepta filtros opcionales `organization_id`, `status`, `method`, `date_from`, `date_to`, `patient`, `booking_id` y `practitioner_id`. La respuesta serializa datos legibles de cita, paciente, profesional, servicio, organización, sede y consultorio, además de monto, moneda, vencimiento, evidencia, revisión y estado; no expone `schema_name`.

`approve` y `reject` trazan revisión en `payment_reviews`, actualizan `payment_attempts.status`, `payment_attempts.reviewed_at` y `bookings.payment_status`. No cambian `bookings.status`, no liberan cupos y no ejecutan automatizaciones externas.
