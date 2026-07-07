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

## 12.1. tenant_payment_settings

```text
id
allow_gateway_payment
allow_manual_transfer
allow_pay_at_location
require_payment_before_confirmation
auto_confirm_gateway_payments
require_manual_review_for_transfers
payment_evidence_due_minutes
manual_review_due_policy
manual_review_due_time
manual_review_business_days_only
auto_expire_if_no_evidence
auto_expire_if_review_overdue
refund_policy_days
refund_policy_message
```

## 12.2. payment_attempts

```text
id
booking_id
method
provider
amount_expected
amount_received nullable
currency
status
external_reference nullable
payment_url nullable
expires_at nullable
created_at
updated_at
```

`method`:

```text
gateway
manual_transfer
pay_at_location
simulated
```

`status`:

```text
pending
pending_evidence
evidence_uploaded
pending_manual_review
review_overdue
approved
rejected
paid
failed
expired_no_evidence
expired
pay_at_location
```

## 12.3. payment_evidence

```text
id
payment_attempt_id
file_url
file_type
uploaded_by
uploaded_at
ai_extracted_data
ai_prevalidation_status
ai_prevalidation_notes
```

## 12.4. payment_reviews

```text
id
payment_attempt_id
reviewed_by
reviewed_at
decision
notes
confirmed_against_bank
previous_status
new_status
```

`decision`:

```text
approved
rejected
needs_more_evidence
```

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
