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

`approve` y `reject` deben delegar en `PaymentReviewService`; aplican solo a intentos `transfer` con `status = evidence_received`, trazan revisión en `payment_reviews`, actualizan `payment_attempts.status`, `payment_attempts.reviewed_at`, `payment_attempts.reviewed_by_user_id` cuando exista y `bookings.payment_status`. No cambian `bookings.status`, no liberan cupos y no ejecutan automatizaciones externas.

### Ajustes UX PR #44 — Registro manual administrativo

La UI de Pagos puede crear intentos manuales `transfer` reutilizando `POST /api/admin/payment-attempts` y puede registrar referencia/notas de comprobante reutilizando `POST /api/admin/payment-attempts/{payment_attempt_id}/evidence`. Esta acción no aprueba pagos, no cambia `bookings.status`, no libera cupos y no crea un segundo camino de revisión; la decisión final permanece en `PaymentReviewService`.

## Fase 6B.12 — Pacientes administrativos base

Endpoints funcionales: `GET /api/admin/patients`, `GET /api/admin/patients/{patient_id}`, `POST /api/admin/patients`, `PATCH /api/admin/patients/{patient_id}` y `POST /api/admin/patients/{patient_id}/disable`.

`GET /api/admin/patients` incluye pacientes activos e inactivos para trazabilidad y acepta filtros opcionales `q` por nombre/documento/teléfono/email y `profile_status`. `POST` requiere `full_name`, rechaza campos extra y `schema_name`, asigna `created_from_channel = admin` y `profile_status = minimal`; `document_type`, si se informa, se normaliza a mayúsculas y debe pertenecer al catálogo Colombia/MVP `RC`, `TI`, `CC`, `PAS`, `CE`, `RE`, `PPT`, `SC`, `DNI`, `NIT`, `OTHER`. `PATCH` permite editar datos administrativos básicos y `profile_status`, validado contra `minimal`, `incomplete`, `complete`, `verified` e `inactive`; `document_type` puede ser `null` o un valor del mismo catálogo, y la reactivación MVP usa `profile_status = minimal`. `disable` inactiva lógicamente con `profile_status = inactive` y no borra citas, perfiles, contactos ni otros datos.

Las respuestas no exponen `schema_name` ni información interna del tenant.

## Fase 6B.13 — Citas virtuales con link manual derivadas desde sede

`POST /api/admin/appointments` mantiene `location_id` obligatorio y no acepta `modality` como campo externo. La modalidad persistida en `bookings.modality` se deriva exclusivamente de `locations.is_virtual`: `true → virtual`, `false → in_person`.

Para sedes virtuales, `room_id` debe ser `null` y la API acepta únicamente datos manuales de link virtual en columnas de `bookings`: `virtual_meeting_url`, `virtual_meeting_id`, `virtual_access_code`, `virtual_link_status`, `virtual_link_created_mode`, `virtual_link_provider` y `virtual_link_sent_at`. El MVP solo permite `virtual_link_provider = manual` y `virtual_link_created_mode = manual`. `virtual_meeting_url` es el dato mínimo para considerar que el link existe: una cita virtual sin URL queda `pending`; guardar una URL manual queda `created`; marcar enviado exige URL, queda `sent` y completa `virtual_link_sent_at`. `virtual_meeting_id` y `virtual_access_code` son auxiliares y no bastan por sí solos para pasar a `created` o `sent`.

Para sedes presenciales, la API rechaza datos de link virtual y devuelve `virtual_link_status = not_applicable`. Al cancelar una cita virtual con link, el estado del link pasa a `cancelled`.

## Fase 6D.1 — Dashboard administrativo real

`GET /api/admin/dashboard/summary` requiere auth admin real y `X-TotalChat-Tenant-Id`. El backend resuelve el tenant con la dependencia admin existente y ejecuta las consultas dentro del contexto tenant-scoped; no acepta ni serializa `schema_name`.

El contrato devuelve métricas operativas mínimas: `appointments_today`, `upcoming_appointments`, `appointments_pending_payment`, `payment_reviews_pending`, `virtual_appointments_without_link`, `active_services` y `active_practitioners`. Además devuelve listas limitadas y legibles para `today_appointments`, `pending_payment_reviews` y `virtual_link_alerts`.

`payment_reviews_pending` cuenta solo intentos `transfer` con `status = evidence_received` y `evidence_received_at` presente. `virtual_appointments_without_link` cuenta solo citas `scheduled` de modalidad `virtual` sin `virtual_meeting_url`. La pantalla frontend consume este contrato con token y tenant activo existentes.
