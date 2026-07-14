# DATA_MODEL.md  
# Modelo de Datos Conceptual de TotalChat

## 1. Principio general

TotalChat usará PostgreSQL con:

- Schema `public` para control SaaS.
- Un schema por tenant para datos operativos.
- pgvector para búsqueda semántica.

El modelo prioriza:

- Multi-tenancy.
- Flexibilidad comercial.
- Snapshot histórico.
- Auditoría.
- Seguridad.
- Evolución futura.

---

# 2. Schema public

## 2.1. tenants

Representa cada cliente de TotalChat.

Campos conceptuales:

```text
id
name
slug
schema_name
status
plan_id
created_at
updated_at
```

## 2.2. tenant_channels

Canales configurados por tenant.

```text
id
tenant_id
channel_type
external_identifier
webhook_secret_hash
settings
is_active
created_at
updated_at
```

`channel_type`:

```text
telegram
whatsapp
web
```

## 2.3. tenant_domains

Dominios o subdominios del tenant.

```text
id
tenant_id
domain
is_primary
status
```

## 2.4. users

Usuarios administrativos.

```text
id
email
password_hash
full_name
status
created_at
updated_at
```

## 2.5. user_tenants

Relación usuario-tenant.

```text
user_id
tenant_id
role
status
```

Roles:

```text
owner
admin
staff
readonly
```

## 2.6. plans / subscriptions

Para futuro manejo SaaS.

```text
plans
subscriptions
```

---

# 3. Schema tenant

Cada tenant tiene su propio schema.

Ejemplo:

```text
tenant_dra_ana
tenant_clinica_vida
```

---

# 4. Organizaciones y ubicaciones

## 4.1. organizations

```text
id
name
organization_type
legal_name
tax_id
email
phone
status
created_at
updated_at
```

`organization_type`:

```text
independent_practitioner
clinic
health_center
office
other
```

## 4.2. locations

```text
id
organization_id
name
address
city
neighborhood
reference
is_virtual
status
created_at
updated_at
```

## 4.3. rooms

```text
id
location_id
name
room_type
capacity
status
created_at
updated_at
```

---

# 5. Profesionales y especialidades

## 5.1. practitioners

```text
id
full_name
professional_type
professional_license
email
phone
status
created_at
updated_at
```

## 5.2. organization_practitioners

```text
organization_id
practitioner_id
role
status
```

## 5.3. specialties

```text
id
name
description
status
```

## 5.4. practitioner_specialties

```text
practitioner_id
specialty_id
status
```

---

# 6. Servicios

## 6.1. service_catalog

Catálogo opcional de referencia, sin precio obligatorio.

```text
id
name
description
specialty_id
status
```

## 6.2. practitioner_services

Entidad central de lo reservable.

```text
id
organization_id
practitioner_id
service_catalog_id nullable
name
description
duration_minutes
requires_payment
status
created_at
updated_at
```

No debe tener precio único rígido.

## 6.3. service_modalities

```text
id
practitioner_service_id
modality
location_id nullable
room_id nullable
status
```

`modality`:

```text
in_person
virtual
both
```

---

# 7. Precios y condiciones comerciales

## 7.1. Modelo jerárquico

El precio se basa en:

```text
payer_type → payer → payer_plan → practitioner_service_price
```

Ejemplo:

```text
Particular
  → Particular
    → Tarifa particular

Medicina prepagada
  → Sura
    → Póliza básica
    → Póliza mejorada

Medicina prepagada
  → Colsanitas
    → Plan inicial
    → Plan avanzado

Póliza de salud
  → Aseguradora ABC
    → Plan pequeño
```

## 7.2. payer_types

```text
id
code
name
description
status
```

Ejemplos:

```text
particular
eps
medicina_prepagada
poliza_salud
convenio_empresarial
otro
```

## 7.3. payers

```text
id
payer_type_id
name
description
status
```

Ejemplos:

```text
Particular
Sura
Colsanitas
Aseguradora ABC
Nueva EPS
Empresa XYZ
```

## 7.4. payer_plans

```text
id
payer_id
name
description
status
```

Ejemplos:

```text
Tarifa particular
Póliza básica
Póliza mejorada
Plan inicial
Plan avanzado
Plan pequeño
```

## 7.5. practitioner_service_prices

Precio específico por servicio del profesional y plan.

```text
id
practitioner_service_id
payer_plan_id
price
currency
valid_from
valid_to
status
```

## 7.6. patient_payer_profiles

Planes o coberturas declaradas/asociadas al paciente.

```text
id
patient_id
payer_plan_id
member_id nullable
status
validation_status
valid_from
valid_to
created_at
updated_at
```

`validation_status`:

```text
declared
pending_validation
validated
rejected
expired
```

---

# 8. Pacientes

## 8.1. patients

```text
id
full_name
phone nullable
email nullable
document_type nullable
document_number nullable
profile_status
created_from_channel
created_at
updated_at
```

`profile_status`:

```text
minimal
incomplete
complete
verified
inactive
```

## 8.2. patient_contacts

```text
id
patient_id
channel_type
value
external_id nullable
is_primary
is_verified
status
```

## 8.3. required_patient_fields

Configuración por tenant de datos obligatorios por etapa.

```text
id
field_code
required_stage
is_required
status
```

`required_stage`:

```text
before_booking
before_payment
before_confirmation
before_appointment
before_invoice
at_reception
```

---

# 9. Disponibilidad

## 9.1. availability_rules

```text
id
organization_id
practitioner_id
practitioner_service_id nullable
location_id nullable
room_id nullable
modality
weekday
start_time
end_time
valid_from
valid_to
buffer_minutes
status
```

## 9.2. availability_exceptions

```text
id
practitioner_id
location_id nullable
room_id nullable
starts_at
ends_at
exception_type
reason
status
```

`exception_type`:

```text
vacation
sick_leave
administrative_block
special_schedule
holiday
manual_block
```

---

# 10. Citas

## 10.1. bookings

```text
id
organization_id
patient_id
practitioner_id
practitioner_service_id
payer_type_id nullable
payer_id nullable
payer_plan_id nullable
location_id nullable
room_id nullable
modality
starts_at
ends_at
status
payment_status
attendance_confirmation_status
service_name_snapshot
duration_minutes_snapshot
practitioner_name_snapshot
payer_type_name_snapshot nullable
payer_name_snapshot nullable
payer_plan_name_snapshot nullable
price_snapshot
currency_snapshot
total_amount
address_snapshot nullable
room_snapshot nullable
created_channel
pending_patient_data
created_at
updated_at
```

## 10.2. booking_status_history

```text
id
booking_id
previous_status
new_status
changed_by_type
changed_by_id nullable
reason
created_at
```

## 10.3. Estados de cita

```text
draft
tentative
pending_payment
pending_payment_evidence
pending_manual_payment_review
confirmed
confirmed_without_payment
cancelled
cancelled_by_patient
cancelled_by_admin
rescheduled
completed
no_show
expired_no_evidence
expired
```

---

# 11. Citas virtuales

## 11.1. booking_virtual_details

```text
id
booking_id
provider
meeting_url
meeting_id
access_code
status
created_mode
created_at
updated_at
```

`provider`:

```text
manual
teams
google_meet
zoom
jitsi
other
```

`status`:

```text
pending
created
sent
cancelled
failed
```

`created_mode`:

```text
manual
automatic
external
```

---

# 12. Pagos

El baseline implementado de pagos es manual/simulado. No incluye Wompi, pasarelas, tarjetas ni conciliación bancaria automática.

## 12.1. payment_settings

```text
id
organization_id
allow_transfer
allow_simulated_payment
allow_pay_on_site
evidence_deadline_minutes
manual_review_deadline_minutes
release_slot_on_missing_evidence
release_slot_on_review_overdue
status
created_at
updated_at
```

Notas:

- `release_slot_on_review_overdue` debe ser `false` por defecto.
- Campos conceptuales anteriores como `allow_gateway_payment`, `auto_confirm_gateway_payments` o políticas de pasarela quedan reservados para una fase futura de Wompi/pasarela.

## 12.2. payment_attempts

```text
id
booking_id
method
amount
currency
status
expires_at nullable
evidence_received_at nullable
reviewed_at nullable
reviewed_by_user_id nullable
created_at
updated_at
```

`method`:

```text
transfer
simulated
pay_on_site
```

`status`:

```text
pending
evidence_required
evidence_received
under_review
approved
rejected
expired
cancelled
simulated_approved
```

Notas:

- `pending` se usa actualmente para intentos `pay_on_site`.
- `under_review` y `cancelled` están implementados/reservados para flujos futuros o acciones explícitas de dominio.

## 12.3. payment_evidence

```text
id
payment_attempt_id
storage_object_key
original_filename nullable
content_type nullable
uploaded_at
uploaded_channel nullable
notes nullable
```

La IA puede almacenar extracción/prevalidación en campos futuros o metadatos si una spec posterior lo define, pero esa prevalidación nunca aprueba el pago.

## 12.4. payment_reviews

```text
id
payment_attempt_id
decision
reviewer_user_id nullable
reviewed_at
notes nullable
created_at
```

`decision`:

```text
approved
rejected
```

Notas:

- `confirmed_against_bank` es un endurecimiento opcional/futuro para políticas de revisión bancaria más estrictas; no bloquea el MVP manual/simulado actual salvo que una spec futura lo agregue.
- La auditoría de revisión vive en PostgreSQL dentro del schema del tenant.

## 12.5. refunds

```text
id
booking_id
payment_attempt_id
amount
currency
status
reason
due_days
processed_at
notes
```

---

# 13. Recordatorios

## 13.1. appointment_confirmation_settings

```text
id
enabled
reminder_hours_before
require_attendance_confirmation
second_confirmation_on_negative_response
no_response_policy
no_response_deadline_hours_before
auto_cancel_on_no_response
refund_policy_days
refund_policy_message
```

`no_response_policy`:

```text
mark_unconfirmed
send_second_reminder
notify_admin
auto_cancel
```

---

# 14. Conversaciones

## 14.1. conversation_sessions

```text
id
channel_type
external_user_id
patient_id nullable
booking_id nullable
status
state
created_at
updated_at
```

## 14.2. messages

```text
id
conversation_session_id
direction
message_type
content
raw_payload
intent nullable
tool_calls nullable
created_at
```

---

# 15. Semántica y pgvector

## 15.1. semantic_documents

```text
id
source_type
source_id
content
metadata
embedding
embedding_provider
embedding_model
embedding_version
status
created_at
updated_at
```

Usos:

- Servicios.
- Especialidades.
- FAQ.
- Políticas.
- Instrucciones.

---

# 16. Eventos

## 16.1. domain_events

```text
id
event_type
aggregate_type
aggregate_id
payload
status
created_at
processed_at nullable
```

Ejemplos:

```text
booking.created
booking.confirmed
payment.evidence_uploaded
payment.review_overdue
reminder.due
attendance.confirmed
attendance.declined
virtual_link.pending
```

# 17. Integraciones externas de agenda, calendario y reuniones

## 17.1. external_systems

Representa sistemas externos configurados por tenant.

```text
id
system_type
name
status
auth_type
settings
created_at
updated_at
```

`system_type`:

```text
docplanner
google_calendar
microsoft_calendar
microsoft_teams
zoom
other
```

## 17.2. scheduling_provider_configs

Define el proveedor de agenda activo por tenant, organización o profesional.

```text
id
organization_id nullable
practitioner_id nullable
provider_type
external_system_id nullable
authority_mode
sync_mode
status
settings
created_at
updated_at
```

`provider_type`:

```text
internal
docplanner
google_calendar
microsoft_calendar
other
```

`authority_mode`:

```text
internal_authoritative
external_authoritative
hybrid
```

`sync_mode`:

```text
none
read_only
write_through
bidirectional
```

## 17.3. meeting_provider_configs

Define proveedor de reuniones virtuales.

```text
id
organization_id nullable
practitioner_id nullable
provider_type
external_system_id nullable
status
settings
created_at
updated_at
```

`provider_type`:

```text
manual
google_meet
microsoft_teams
zoom
other
```

## 17.4. external_practitioner_mappings

```text
id
practitioner_id
external_system_id
external_practitioner_id
raw_external_payload
status
last_synced_at
```

## 17.5. external_location_mappings

```text
id
location_id nullable
room_id nullable
external_system_id
external_location_id nullable
external_calendar_id nullable
external_address_id nullable
raw_external_payload
status
last_synced_at
```

## 17.6. external_service_mappings

```text
id
practitioner_service_id
external_system_id
external_service_id nullable
external_address_service_id nullable
raw_external_payload
status
last_synced_at
```

## 17.7. external_booking_mappings

```text
id
booking_id
external_system_id
external_booking_id nullable
external_event_id nullable
external_status
raw_external_payload
last_synced_at
created_at
updated_at
```

## 17.8. external_events

```text
id
external_system_id
event_type
external_event_id nullable
payload
processing_status
received_at
processed_at nullable
error_message nullable
```

## 17.9. external_sync_runs

```text
id
external_system_id
sync_type
started_at
finished_at
status
summary
error_message nullable
```

`sync_type`:

```text
initial_import
slots_sync
bookings_sync
calendar_blocks_sync
callbacks_pull
manual_reconciliation
```

# Modelo multi-solución en public schema

TotalChat debe reconocer que un tenant puede tener una o varias soluciones activas.

## solutions

```text
id
code
name
description
status
created_at
updated_at
```

Códigos oficiales iniciales:

```text
medichat
restochat
hotelchat
staychat
storechat
```

## tenant_solutions

```text
id
tenant_id
solution_id
status
settings
created_at
updated_at
```

Para MVP:

```text
tenant_solutions = medichat
```

Futuro:

Un mismo tenant podría tener más de una solución.

Ejemplo:

```text
Tenant Club Campestre
├── RestoChat
├── HotelChat
└── StayChat
```

## Regla de datos por vertical

El dominio médico documentado actualmente pertenece a MediChat.

Por tanto:

- patients = MediChat;
- practitioners = MediChat;
- specialties = MediChat;
- payer_types/payers/payer_plans de salud = MediChat;
- appointments/bookings médicos = MediChat.

Las capacidades comunes como pagos, conversaciones, canales, providers y eventos pueden vivir en platform/core.

# Modelo de campañas y comunicados

El módulo de campañas debe ser transversal.

Tablas principales:

```text
campaigns
campaign_audiences
campaign_recipients
campaign_deliveries
contact_preferences
campaign_templates
campaign_events
```

## campaigns

```text
id
tenant_id
solution_code nullable
name
description nullable
campaign_type
message_type
status
send_mode
scheduled_at nullable
timezone
message_body
target_channel_policy
audience_type
audience_filters
estimated_recipients
eligible_recipients
blocked_recipients
created_by
approved_by nullable
approved_at nullable
sent_at nullable
cancelled_at nullable
created_at
updated_at
```

## contact_preferences

```text
id
tenant_id
solution_code nullable
contact_type
contact_id
channel_type
allow_transactional
allow_operational
allow_marketing
opted_out_at nullable
opt_out_reason nullable
source
created_at
updated_at
```

Regla:

Los mensajes de marketing requieren `allow_marketing=true`.

## Nota Fase 6B.4 — Especialidades y `room_type`

`specialties` continúa siendo tenant-scoped y conserva `status` para activación/inactivación reversible. `practitioner_specialties` continúa normalizado con unicidad por `(practitioner_id, specialty_id)` y `status` para retirar/restaurar asignaciones sin crear duplicados ni eliminar la especialidad maestra.

`rooms.room_type` permanece como columna textual para preservar datos históricos, pero nuevas escrituras administrativas validan el catálogo fijo inicial: `consulta_general`, `procedimientos`, `terapia`, `diagnostico`, `virtual`, `otro`. La fase no introduce CRUD de tipos de consultorio ni relaciona el tipo con servicios, precios o disponibilidad.

## 5.2.1. Fase 6B.5 — relación organización-profesional

`organization_practitioners` materializa la relación muchos-a-muchos entre organizaciones y profesionales dentro del schema tenant antes del CRUD de Servicios del profesional.

Campos implementados:

```text
organization_id -> organizations.id
practitioner_id -> practitioners.id
role
status
created_at
updated_at
```

Reglas:

- `organization_id + practitioner_id` es único y no se crean duplicados.
- `status` usa borrado lógico: `active` / `inactive`.
- `role` usa catálogo fijo inicial: `primary`, `member`, `external`; el default es `member`.
- No hay borrado físico ni autorización basada en `role` en esta fase.
- Organizaciones o profesionales inactivos no pueden usarse para nuevas asociaciones activas.
- Las relaciones existentes se conservan y pueden listarse aunque la organización o el profesional se inactive después.
- Fase 6B.6 deberá validar que `PractitionerService.organization_id + practitioner_id` exista y esté activa en `organization_practitioners` antes de crear servicios.


## Fase 6B.6 — PractitionerService operativo

`practitioner_services` representa el servicio que presta un profesional dentro de una organización. Campos usados en esta fase: `id`, `organization_id`, `practitioner_id`, `name`, `description`, `duration_minutes`, `requires_payment`, `status`, `created_at`, `updated_at`.

Reglas: crear o reactivar un servicio depende de que `organization_practitioners` exista y esté activa para la misma pareja `organization_id + practitioner_id`, y de que organización y profesional estén activos. Servicios existentes no se borran ni desaparecen si se inactivan sus padres o la relación. La validación de duplicados es de aplicación para nombre normalizado case-insensitive por organización y profesional. Servicios no incluye precios, modalidades ni disponibilidad todavía.


## Fase 6B.7 — Base comercial de pagadores y planes

`payer_types`, `payers` y `payer_plans` forman la jerarquía comercial previa a tarifas. `payer_types.code` se normaliza; `payers.name` es único por tipo con comparación normalizada/case-insensitive; `payer_plans.name` es único por pagador con comparación normalizada/case-insensitive. La activación de hijos depende de padres activos, sin borrado físico ni configuración de precios en esta fase.

## Fase 6B.8 — PractitionerServicePrice

`practitioner_service_prices` representa una tarifa manual para la combinación **PractitionerService + PayerPlan**. Usa los campos existentes `id`, `practitioner_service_id`, `payer_plan_id`, `price`, `currency`, `valid_from`, `valid_to` y `status`.

Se mantiene la unicidad por `practitioner_service_id + payer_plan_id + valid_from`. Adicionalmente, la aplicación valida que no existan dos precios **activos** del mismo servicio y plan con vigencias solapadas; `valid_to = null` significa rango abierto. Los históricos inactivos pueden permanecer aunque se solapen.

TotalChat / MediChat asume una moneda operativa única por tenant. Para Fase 6B.8 no se crean `tenant_settings` ni `organization_settings`; COP es el default técnico temporal de consola. No hay multi-moneda por precio, tasas de cambio ni conversión.

### 9.3. Disponibilidad base administrativa (Fase 6B.9)

La administración de disponibilidad base usa reglas recurrentes persistentes para indicar cuándo un profesional podría atender dentro de una organización, opcionalmente para un servicio específico del profesional. La convención administrativa de `day_of_week` es `0 = Monday/Lunes` y `6 = Sunday/Domingo`; la implementación histórica de agenda puede mantener columnas internas existentes, pero el contrato admin expone esta convención estable.

TotalChat/MediChat usará un modelo híbrido de agenda:

- Las reglas de disponibilidad se guardan como configuración persistente.
- Los slots disponibles se calcularán bajo demanda a partir de reglas, bloqueos, reservas, citas y agendas externas futuras.
- Las reservas/citas/holds sí se persistirán en fases posteriores para proteger horarios y auditar estados.
- Esta fase no crea reservas, citas ni slots físicos.

### Fase 6B.9.1 — Bloqueos e indisponibilidad

La disponibilidad base define elegibilidad de atención. Los bloqueos/indisponibilidades reducen esa elegibilidad para rangos futuros donde un profesional no puede atender, aunque sus reglas recurrentes indiquen que normalmente podría hacerlo. Las reservas, citas y holds serán los registros que ocupen realmente un horario en fases posteriores; esta fase no calcula slots, no crea citas y no crea reservas.

La consola administra bloqueos con profesional, sede opcional, consultorio opcional, inicio, fin, tipo controlado por backend, motivo opcional y estado activo/inactivo. No hay borrado físico. Los tipos de bloqueo del MVP son controlados para preservar semántica operativa y facilitar reglas futuras; la configuración dinámica por tenant queda como mejora futura.

## Fase 6B.10 — Citas administrativas

La fase reutiliza `bookings` como registro persistente alineado para citas administrativas, evitando duplicar modelos de ocupación de horario. Para el contrato administrativo de Citas se usan los campos `organization_id`, `location_id`, `room_id`, `practitioner_id`, `practitioner_service_id`, `patient_id`, `starts_at`, `ends_at`, `status`, `notes`, `created_at` y `updated_at`.

Estados administrativos de esta fase:

- `scheduled`: ocupa horario real y bloquea nuevas citas solapadas del profesional y del consultorio cuando aplica.
- `cancelled`, `completed`, `no_show`: conservan trazabilidad pero no ocupan horario para nuevas citas.

La validación de solapamiento usa rangos estándar: `existing.starts_at < new.ends_at` y `new.starts_at < existing.ends_at`. También se validan bloqueos activos aplicables del profesional en alcance general, sede o consultorio.

### Migración tenant bajo demanda para `bookings.notes`

La columna `bookings.notes` se agrega a tenants existentes mediante el comando explícito `python3 -m app.tenancy.migrate_existing_tenants`. La migración registra `007_booking_notes` en `tenant_schema_migrations` y es idempotente. No se ejecuta automáticamente en cada arranque del backend.

## Fase 6B.11 — Estados de pago administrativos

La pantalla administrativa de pagos reutiliza las tablas tenant-scoped existentes `payment_attempts`, `payment_evidence` y `payment_reviews`.

Estados operativos esperados para `payment_attempts.status` en esta fase: `pending`, `evidence_required`, `evidence_received`, `under_review`, `approved`, `rejected`, `expired`, `cancelled` y `simulated_approved`.

Valores de `bookings.payment_status` usados por la revisión manual: `pending` para pagos no resueltos, `paid` cuando `PaymentReviewService` aprueba un intento `transfer` con evidencia recibida y `rejected` cuando lo rechaza. Esta fase no agrega expiración automática, reembolsos, conciliación bancaria ni pasarelas reales.

## Pacientes administrativos — Fase 6B.12

`patients` conserva datos administrativos mínimos del paciente por schema tenant. En Fase 6B.12 `document_type` no es texto libre: usa catálogo controlado Colombia/MVP con valores `RC`, `TI`, `CC`, `PAS`, `CE`, `RE`, `PPT`, `SC`, `DNI`, `NIT`, `OTHER`; no se valida edad, nacionalidad, longitud/formato del número ni fuentes externas. Los estados válidos de `profile_status` para la consola son:

- `minimal`
- `incomplete`
- `complete`
- `verified`
- `inactive`

Crear desde consola usa `created_from_channel = admin` y `profile_status = minimal`. La inactivación es lógica (`inactive`) y no modifica citas históricas, perfiles de pagador ni contactos existentes. La reactivación se realiza actualizando `profile_status` a un estado permitido no inactivo; el MVP usa `minimal` cuando no hay criterio adicional documentado.

## Citas virtuales MVP y modalidad por sede

Para citas administrativas, la sede define la modalidad: `locations.is_virtual = true` implica `bookings.modality = virtual`, y `locations.is_virtual = false` implica `bookings.modality = in_person`. No hay selector libre de modalidad en la experiencia admin.

Los datos de link virtual manual permanecen en `bookings` mediante columnas como `virtual_meeting_url`, `virtual_meeting_id`, `virtual_access_code`, `virtual_link_status`, `virtual_link_created_mode`, `virtual_link_provider` y `virtual_link_sent_at`. En el MVP, `virtual_meeting_url` es el dato mínimo para considerar el link creado o enviado; `virtual_meeting_id` y `virtual_access_code` son auxiliares. No se crea `booking_virtual_details` en este MVP.
