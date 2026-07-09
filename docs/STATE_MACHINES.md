# STATE_MACHINES.md
# Máquinas de estado y transiciones permitidas en TotalChat

## 1. Propósito

Este documento define estados y transiciones obligatorias para citas, pagos, evidencia, revisión manual, confirmación de asistencia, reembolsos y citas virtuales.

Codex debe implementar estas transiciones como reglas de dominio, no como simples cambios libres de string.

## 2. Principios

1. Los estados críticos no se modifican directamente desde controladores.
2. Toda transición debe pasar por un servicio de dominio.
3. Toda transición debe auditarse.
4. Las transiciones inválidas deben fallar con `BUSINESS_RULE_VIOLATION`.
5. El estado de una cita no debe contradecir el estado de pago.
6. El estado de una cita con agenda externa no debe contradecir el estado del proveedor externo.
7. Una transición no debe saltarse políticas configuradas por tenant.

## 3. Máquina de estado de Booking

### 3.1. Estados

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
rejected_payment
review_overdue
auto_cancelled_no_confirmation
```

### 3.2. Significado

#### draft

Cita en borrador. No debe bloquear agenda ni considerarse reserva.

#### tentative

Cita pre-reservada o en hold. Puede tener slot protegido temporalmente.

#### pending_payment

Cita pendiente de seleccionar o completar pago.

#### pending_payment_evidence

Paciente eligió transferencia y debe enviar evidencia dentro del plazo.

#### pending_manual_payment_review

Paciente envió evidencia y el pago requiere revisión administrativa.

El slot debe permanecer protegido.

#### confirmed

Cita confirmada.

#### confirmed_without_payment

Cita confirmada sin pago previo porque el tenant permite pago en sitio o confirmación sin pago.

#### cancelled_by_patient

Paciente canceló, incluyendo cancelación tras segunda confirmación de no asistencia.

#### cancelled_by_admin

Administrador canceló.

#### rescheduled

Cita fue reprogramada. Puede conservar referencia histórica.

#### completed

Cita realizada.

#### no_show

Paciente no asistió.

#### expired_no_evidence

La cita expiró porque el paciente no envió evidencia de transferencia dentro del plazo.

#### review_overdue

La revisión administrativa está vencida. No libera slot automáticamente salvo configuración explícita.

#### auto_cancelled_no_confirmation

Cita cancelada automáticamente por falta de confirmación de asistencia, solo si el tenant activó esa política.

### 3.3. Transiciones permitidas

```text
draft → tentative
tentative → pending_payment
tentative → confirmed_without_payment
tentative → confirmed
tentative → cancelled_by_admin
tentative → expired

pending_payment → pending_payment_evidence
pending_payment → confirmed
pending_payment → confirmed_without_payment
pending_payment → cancelled_by_patient
pending_payment → cancelled_by_admin
pending_payment → expired

pending_payment_evidence → pending_manual_payment_review
pending_payment_evidence → expired_no_evidence
pending_payment_evidence → cancelled_by_patient
pending_payment_evidence → cancelled_by_admin

pending_manual_payment_review → confirmed
pending_manual_payment_review → rejected_payment
pending_manual_payment_review → review_overdue
pending_manual_payment_review → cancelled_by_admin

review_overdue → confirmed
review_overdue → rejected_payment
review_overdue → pending_manual_payment_review
review_overdue → cancelled_by_admin

confirmed → cancelled_by_patient
confirmed → cancelled_by_admin
confirmed → rescheduled
confirmed → completed
confirmed → no_show
confirmed → auto_cancelled_no_confirmation

confirmed_without_payment → cancelled_by_patient
confirmed_without_payment → cancelled_by_admin
confirmed_without_payment → rescheduled
confirmed_without_payment → completed
confirmed_without_payment → no_show
confirmed_without_payment → auto_cancelled_no_confirmation

rescheduled → confirmed
rescheduled → cancelled_by_patient
rescheduled → cancelled_by_admin

rejected_payment → pending_payment
rejected_payment → cancelled_by_admin
rejected_payment → expired

cancelled_by_patient → terminal
cancelled_by_admin → terminal
completed → terminal
no_show → terminal
expired_no_evidence → terminal
expired → terminal
auto_cancelled_no_confirmation → terminal
```


### 3.4. Transiciones prohibidas

```text
expired_no_evidence → confirmed
cancelled_by_patient → confirmed
cancelled_by_admin → confirmed
completed → cancelled
no_show → confirmed
confirmed → tentative
review_overdue → expired_no_evidence
```

Si se requiere recuperar una cita terminal, debe crearse una nueva cita o un flujo explícito de reapertura aprobado en una spec futura.

## 4. Máquina de estado de PaymentAttempt

### 4.1. Estados implementados/spec 007

```text
evidence_required
evidence_received
approved
rejected
expired
simulated_approved
```

### 4.2. Transiciones

```text
evidence_required → evidence_received
evidence_required → expired

evidence_received → approved
evidence_received → rejected
evidence_received → expired
```

`simulated_approved` se produce únicamente para `method=simulated` y debe distinguirse de aprobación bancaria/manual real.

### 4.3. Reglas

1. Transferencia manual no pasa a `approved` sin revisión administrativa.
2. Evidencia recibida no aprueba pago por sí sola.
3. IA no produce `approved` ni `simulated_approved` como decisión propia.
4. Si falta evidencia, el intento puede pasar a `expired`; la cita libera slot solo según `release_slot_on_missing_evidence`.
5. Revisión vencida no libera automáticamente salvo `release_slot_on_review_overdue=true`.
6. Si `approved` y la cita requiere pago, la cita puede pasar a `confirmed` mediante servicios de dominio.

### 4.4. Mapeo desde estados conceptuales anteriores

| Conceptual anterior | Estado implementado/spec 007 |
|---|---|
| `pending_evidence` | `evidence_required` |
| `evidence_uploaded` | `evidence_received` |
| `pending_manual_review` | `evidence_received` + trabajo de revisión pendiente |
| `review_overdue` | señal/flag/consulta de revisión vencida, no estado runtime nuevo salvo spec futura |
| `paid` | `approved` o `simulated_approved` según método |
| `expired_no_evidence` | `expired` |
| `pay_at_location` | `method=pay_on_site` con transición de booking según política |
| `failed` | `rejected` o `expired` según causa |

No se deben inventar nuevos estados runtime fuera de esta lista sin una spec futura.

## 5. Máquina de evidencia de pago

### 5.1. Estados conceptuales

```text
not_required
pending_upload
uploaded
ai_prevalidated
requires_manual_review
accepted_by_admin
rejected_by_admin
needs_replacement
```

### 5.2. Reglas

1. Una evidencia subida no confirma pago.
2. Una evidencia puede tener datos extraídos por IA.
3. La IA puede marcar inconsistencias.
4. El admin decide.
5. Se debe guardar el archivo o referencia segura.
6. Se debe auditar el origen.

## 6. Máquina de revisión manual

### 6.1. Estados

```text
not_required
pending
overdue
approved
rejected
needs_more_evidence
```

### 6.2. Transiciones

```text
pending → approved
pending → rejected
pending → needs_more_evidence
pending → overdue

overdue → approved
overdue → rejected
overdue → needs_more_evidence

needs_more_evidence → pending
```

### 6.3. Reglas

1. Revisión vencida genera alerta.
2. Revisión vencida no libera slot por defecto.
3. Aprobación debe registrar usuario.
4. Rechazo debe registrar motivo.
5. `approved` debe exigir confirmación bancaria si método es transferencia.

## 7. Máquina de confirmación de asistencia

### 7.1. Estados

```text
not_required
pending
reminder_sent
confirmed
declined_pending_second_confirmation
declined_confirmed
no_response
auto_cancelled_no_confirmation
```

### 7.2. Transiciones

```text
not_required → pending
pending → reminder_sent
reminder_sent → confirmed
reminder_sent → declined_pending_second_confirmation
reminder_sent → no_response

declined_pending_second_confirmation → declined_confirmed
declined_pending_second_confirmation → confirmed

no_response → reminder_sent
no_response → auto_cancelled_no_confirmation
no_response → pending
```

### 7.3. Reglas

1. Respuesta negativa inicial no cancela.
2. Debe pedirse segunda confirmación.
3. El mensaje debe advertir liberación de cupo, nueva reserva sujeta a disponibilidad y política de reembolso.
4. No respuesta no cancela salvo política explícita del tenant.
5. Si se cancela por segunda confirmación, liberar slot y crear flujo de reembolso si aplica.

## 8. Máquina de cita virtual

### 8.1. Estados

```text
not_applicable
pending
created
sent
cancelled
failed
```

### 8.2. Transiciones

```text
not_applicable → pending
pending → created
created → sent
created → cancelled
pending → failed
failed → pending
sent → cancelled
```

### 8.3. Reglas

1. MVP soporta `ManualMeetingProvider`.
2. Link manual se guarda como `created`.
3. Al notificar al paciente, pasa a `sent`.
4. Generación automática es futura.
5. Si la cita se cancela, el detalle virtual debe pasar a `cancelled` si aplica.

## 9. Máquina de reembolso

### 9.1. Estados

```text
not_applicable
pending_review
pending_refund
refunded
rejected
cancelled
```

### 9.2. Transiciones

```text
not_applicable → pending_review
pending_review → pending_refund
pending_review → rejected
pending_refund → refunded
pending_refund → rejected
pending_refund → cancelled
```

### 9.3. Reglas

1. Reembolso no se crea si no hubo pago.
2. Si paciente cancela cita pagada, aplicar política del tenant.
3. Mensaje al paciente debe informar plazo configurable.
4. Reembolso puede requerir revisión administrativa.

## 10. Máquina de external booking mapping

### 10.1. Estados

```text
not_applicable
pending_external_create
external_confirmed
external_failed
external_cancelled
external_moved
sync_conflict
requires_reconciliation
```

### 10.2. Reglas

1. Si `schedule_authority=external_authoritative`, TotalChat no confirma localmente sin `external_confirmed`.
2. Si falla proveedor externo, no confirmar cita local.
3. Si evento externo contradice estado local, marcar `sync_conflict`.
4. Conflictos deben ir a reconciliación administrativa.
5. En MVP solo se implementa interno, pero la arquitectura debe permitir esta máquina futura.

## 11. Auditoría obligatoria

Toda transición debe registrar:

```text
entity_type
entity_id
previous_status
new_status
actor_type
actor_id
reason
metadata
created_at
```

`actor_type`:

```text
system
admin_user
patient
external_provider
scheduler
ai_agent
```

La IA no debe ser actor final para aprobaciones de pago ni confirmaciones críticas; solo puede ser actor de sugerencia o interacción conversacional.

## 12. Máquina de estado de campañas

### 12.1. Estados

```text
draft
ready
scheduled
queued
sending
sent
partially_sent
failed
cancelled
paused
requires_approval
approved
rejected
```

### 12.2. Transiciones

```text
draft → ready
draft → cancelled
ready → scheduled
ready → queued
ready → requires_approval
requires_approval → approved
requires_approval → rejected
approved → scheduled
approved → queued
scheduled → queued
scheduled → cancelled
queued → sending
sending → sent
sending → partially_sent
sending → failed
sending → paused
paused → sending
paused → cancelled
```

### 12.3. Reglas

1. Campaña enviada no se edita.
2. Campaña programada puede cancelarse antes de envío.
3. Campaña de marketing debe validar consentimiento.
4. Campaña sin audiencia elegible no debe enviarse.
5. Campaña con fallos parciales queda `partially_sent`.
6. Toda transición debe auditarse.

## 13. Máquina de estado de entregas de campaña

### 13.1. Estados

```text
pending
queued
skipped
sending
sent
delivered
read
failed
cancelled
blocked_by_consent
blocked_by_channel_policy
blocked_by_missing_contact
```

### 13.2. Transiciones

```text
pending → queued
pending → skipped
pending → blocked_by_consent
pending → blocked_by_channel_policy
pending → blocked_by_missing_contact
queued → sending
sending → sent
sending → failed
sent → delivered
delivered → read
queued → cancelled
```

### 13.3. Reglas

1. Un delivery bloqueado por consentimiento no debe enviarse.
2. Un delivery fallido debe conservar error.
3. No todos los canales soportan delivered/read.
4. Cada delivery pertenece a un tenant/campaign.
