# Data Model — 004-admin-console

Ver `docs/DATA_MODEL.md`. Detalles específicos se completarán durante esta spec.

## Fase 6B.5

La consola administra `organization_practitioners` como relación muchos-a-muchos tenant entre `organizations` y `practitioners`, con `role`, `status`, timestamps y restricción única por pareja. Servicios queda para Fase 6B.6 y deberá validar esta relación activa.


## Fase 6B.6 — PractitionerService

La consola administra `PractitionerService` por organización y profesional. La pareja depende de `organization_practitioners` activa para creación/reactivación. Los servicios históricos permanecen listables con padres o relación inactivos. No hay `service_catalog_id`, `price`, `modality`, `availability`, `specialty_id`, `location_id` ni `room_id` en esta fase.

## Fase 6B.7 — PayerType, Payer y PayerPlan

La consola administra `payer_types`, `payers` y `payer_plans` como base comercial previa a tarifas. `PayerType` usa `code`, `name`, `description` y `status`; `code` se normaliza y es único de forma case-insensitive en la aplicación. `Payer` depende de `payer_type_id` y valida nombre único normalizado por tipo. `PayerPlan` depende de `payer_id` y valida nombre único normalizado por pagador.

Crear o reactivar pagadores requiere tipo activo. Crear o reactivar planes requiere pagador activo y tipo activo. No hay borrado físico y los registros históricos siguen listables aunque sus padres queden inactivos. No se implementan precios ni `PractitionerServicePrice` en esta fase.

## Fase 6B.8 — PractitionerServicePrice

La consola administra `PractitionerServicePrice` como tarifa manual para `PractitionerService + PayerPlan`. El modelo conserva `currency`, pero la UI usa COP como moneda operativa temporal y no expone selector editable. No se agregan modelos alternativos de precio ni tablas de configuración de moneda. Los precios activos no pueden solaparse para la misma pareja servicio/plan; los históricos inactivos permanecen listables.

## Fase 6B.9 — PractitionerAvailabilityRule

La consola administra reglas recurrentes de disponibilidad base para profesionales mediante `availability_rules` como configuración persistente tenant-scoped. La UI/API de Fase 6B.9 usa el contrato `PractitionerAvailabilityRule` con `organization_id`, `practitioner_id`, `practitioner_service_id` opcional, `day_of_week`, `start_time`, `end_time`, `valid_from`, `valid_to` opcional y `status`.

Convención: `day_of_week` usa `0 = Monday/Lunes` y `6 = Sunday/Domingo`. `start_time` debe ser menor que `end_time`; no se modelan cruces de medianoche. `valid_to`, si existe, no puede ser anterior a `valid_from`. No hay borrado físico.

Una regla general (`practitioner_service_id = null`) y una regla específica por servicio pueden coexistir; esta fase solo administra reglas y no resuelve prioridad para cálculo futuro de slots.

### Fase 6B.9.1 — Bloqueos e indisponibilidad

La disponibilidad base define elegibilidad de atención. Los bloqueos/indisponibilidades reducen esa elegibilidad para rangos futuros donde un profesional no puede atender, aunque sus reglas recurrentes indiquen que normalmente podría hacerlo. Las reservas, citas y holds serán los registros que ocupen realmente un horario en fases posteriores; esta fase no calcula slots, no crea citas y no crea reservas.

La consola administra bloqueos con profesional, sede opcional, consultorio opcional, inicio, fin, tipo controlado por backend, motivo opcional y estado activo/inactivo. No hay borrado físico. Los tipos de bloqueo del MVP son controlados para preservar semántica operativa y facilitar reglas futuras; la configuración dinámica por tenant queda como mejora futura.

## Fase 6B.10 — Citas administrativas

La consola reutiliza `bookings` como modelo persistente para citas administrativas y agrega `notes` como nota administrativa opcional. No se crea una tabla duplicada de `appointments`.

Estados usados por esta pantalla: `scheduled`, `cancelled`, `completed`, `no_show`. Solo `scheduled` ocupa horario; los demás estados preservan historial sin bloquear nuevas citas.

### Ajuste PR #43 — reprogramación y agenda diaria operativa

La cita administrativa mantiene la misma organización, sede, profesional, servicio y paciente durante esta fase. La reprogramación básica solo cambia rango horario, consultorio y notas para citas `scheduled`; estados no activos solo admiten notas. La agenda diaria muestra slots visuales disponibles calculados desde reglas de disponibilidad base activas del profesional seleccionado, menos bloqueos activos y citas `scheduled`.

## Fase 6B.11 — Pagos administrativos base

La consola administra revisión manual sobre `payment_attempts`, `payment_evidence` y `payment_reviews` existentes. Las evidencias y revisiones no se eliminan físicamente.

Estados de intento reconocidos por la pantalla: `pending`, `evidence_required`, `evidence_received`, `under_review`, `approved`, `rejected`, `expired`, `cancelled` y `simulated_approved`.

Estados de `bookings.payment_status` usados por esta fase: `pending`, `paid` y `rejected`. Aprobar/rechazar pagos no modifica `bookings.status` ni libera horarios automáticamente.
