# TEST_FIXTURES.md
# Fixtures, datos de ejemplo y escenarios de prueba para TotalChat

## 1. Propósito

Este documento define datos de ejemplo y escenarios que deben usarse para pruebas automatizadas, pruebas manuales y validación de Codex.

Los fixtures ayudan a evitar ambigüedad y permiten verificar que el modelo soporta casos reales.

## 2. Principios

1. Los fixtures deben ser reproducibles.
2. No deben contener datos reales de pacientes.
3. Deben cubrir profesional independiente y clínica.
4. Deben cubrir precios jerárquicos.
5. Deben cubrir transferencia, evidencia, revisión y recordatorios.
6. Deben cubrir agenda interna y preparación para agenda externa.
7. Deben cubrir cita presencial y virtual.

## 3. Tenant demo 1: Psicóloga Ana

### 3.1. Tenant

```text
tenant_name = Consultorio Psicóloga Ana
slug = psicologa-ana
schema = tenant_psicologa_ana
timezone = America/Bogota
currency = COP
```

### 3.2. Organización

```text
name = Consultorio Psicóloga Ana
organization_type = independent_practitioner
```

### 3.3. Sede

```text
name = Consultorio Poblado
address = Carrera 43A # 10-15
city = Medellín
neighborhood = El Poblado
reference = Edificio médico, piso 8
is_virtual = false
```

### 3.4. Consultorio

```text
name = Consultorio 801
room_type = consulting_room
capacity = 1
```

### 3.5. Profesional

```text
full_name = Ana Gómez
professional_type = psychologist
professional_license = TP-PSI-12345
```

### 3.6. Especialidad

```text
name = Psicología
```

### 3.7. Servicios

#### Servicio 1

```text
name = Terapia cognitivo conductual
duration_minutes = 60
requires_payment = true
modalities = in_person, virtual
```

#### Servicio 2

```text
name = Terapia de duelo
duration_minutes = 60
requires_payment = true
modalities = virtual
```

#### Servicio 3

```text
name = Consulta inicial
duration_minutes = 45
requires_payment = true
modalities = in_person
```

### 3.8. Jerarquía comercial

#### Payer types

```text
particular = Particular
medicina_prepagada = Medicina prepagada
poliza_salud = Póliza de salud
```

#### Payers

```text
Particular
Sura
Colsanitas
Aseguradora ABC
```

#### Payer plans

```text
Particular / Tarifa particular
Sura / Póliza básica
Sura / Póliza mejorada
Colsanitas / Plan inicial
Colsanitas / Plan avanzado
Aseguradora ABC / Plan pequeño
```

### 3.9. Precios para terapia cognitivo conductual

```text
Particular / Tarifa particular = 180000 COP
Sura / Póliza básica = 130000 COP
Sura / Póliza mejorada = 110000 COP
Colsanitas / Plan inicial = 125000 COP
Colsanitas / Plan avanzado = 100000 COP
Aseguradora ABC / Plan pequeño = 140000 COP
```

### 3.10. Precios para terapia de duelo

```text
Particular / Tarifa particular = 170000 COP
Sura / Póliza básica = 125000 COP
Colsanitas / Plan avanzado = 105000 COP
```

### 3.11. Disponibilidad

```text
Lunes a viernes
08:00 - 12:00
14:00 - 18:00
buffer_minutes = 0
```

### 3.12. Configuración de pagos

```text
allow_gateway_payment = false
allow_manual_transfer = true
allow_pay_at_location = false
require_payment_before_confirmation = true
payment_evidence_due_minutes = 60
manual_review_due_policy = next_business_day_noon
auto_expire_if_no_evidence = true
auto_expire_if_review_overdue = false
refund_policy_days = 5
```


### 3.12.1. Provisioning operativo de tenant

Para pruebas de Fase 6C.1.1, el tenant `clinica-demo` se crea con:

```bash
python3 -m app.tenancy.create_tenant \
  --name "Clínica Demo" \
  --slug clinica-demo
```

La ejecución repetida con el mismo slug debe ser idempotente: no duplica `public.tenants`, no cambia el `schema_name` almacenado, verifica o crea el schema faltante y aplica migraciones pendientes de forma segura. La salida no debe exponer `schema_name`.

### 3.12.2. Usuario administrativo bootstrap

Para pruebas de Fase 6C.1 sobre el tenant `clinica` o fixtures equivalentes:

```text
email = admin@clinica.com
full_name = Admin Clínica
role = owner
password = provista por prompt seguro o TOTALCHAT_BOOTSTRAP_ADMIN_PASSWORD
```

El password debe almacenarse hasheado con bcrypt en `public.users.password_hash`; el valor plano nunca debe quedar en base de datos, logs ni salida del comando.

### 3.13. Confirmación de asistencia

```text
enabled = true
reminder_hours_before = 24
require_attendance_confirmation = true
second_confirmation_on_negative_response = true
no_response_policy = notify_admin
auto_cancel_on_no_response = false
```

### 3.14. Agenda

```text
SchedulingProvider = InternalSchedulingProvider
authority_mode = internal_authoritative
sync_mode = none
MeetingProvider = ManualMeetingProvider
```

## 4. Tenant demo 2: Clínica Vida

### 4.1. Tenant

```text
tenant_name = Clínica Vida
slug = clinica-vida
schema = tenant_clinica_vida
timezone = America/Bogota
currency = COP
```

### 4.2. Organización

```text
name = Clínica Vida
organization_type = clinic
```

### 4.3. Sedes

```text
Sede Poblado
Sede Envigado
Teleconsulta
```

### 4.4. Profesionales

```text
Dr. Carlos Ruiz - Dermatólogo
Dra. Laura Pérez - Médica general
Dra. Mariana Soto - Psicóloga
```

### 4.5. Servicios

```text
Consulta dermatológica - 30 minutos
Control dermatológico - 20 minutos
Consulta medicina general - 30 minutos
Terapia psicológica - 60 minutos
```

### 4.6. Planes

```text
Particular / Tarifa particular
Sura / Póliza básica
Sura / Póliza mejorada
Colsanitas / Plan inicial
Colsanitas / Plan avanzado
Nueva EPS / Plan contributivo
```

### 4.7. Reglas esperadas

- No todos los profesionales aceptan todos los planes.
- No todos los servicios tienen las mismas tarifas.
- Un servicio puede ser presencial en una sede y virtual en otra.
- La disponibilidad depende de profesional, sede, consultorio y servicio.

## 5. Tenant demo 3: Doctor con Docplanner futuro

Este fixture no debe implementarse completo en MVP, pero sirve para validar diseño.

```text
tenant_name = Doctor con Docplanner
schedule_authority = docplanner
authority_mode = external_authoritative
sync_mode = bidirectional
```

Reglas esperadas:

- BookingService usa SchedulingProvider.
- Provider fake simula Docplanner.
- No se confirma cita local sin confirmación externa.
- Se guarda external_booking_mapping.

## 6. Pacientes de prueba

### Paciente mínimo nuevo

```text
full_name = Juan Pérez
phone = +573001112233
email = null
document_type = null
document_number = null
profile_status = minimal
```

### Paciente con cobertura declarada

```text
full_name = María Gómez
phone = +573004445566
payer_plan = Colsanitas / Plan avanzado
member_id = COL-123456
validation_status = declared
profile_status = incomplete
```

### Paciente particular

```text
full_name = Carlos Martínez
phone = +573007778899
payer_plan = Particular / Tarifa particular
profile_status = minimal
```

## 7. Escenarios de prueba obligatorios

### Escenario 1: reserva particular presencial

1. Paciente nuevo solicita terapia cognitivo conductual.
2. Indica particular.
3. Sistema muestra precio particular.
4. Sistema ofrece slots.
5. Paciente selecciona slot.
6. Sistema crea cita tentativa con snapshot.
7. Sistema crea intento de transferencia.
8. Cita queda pending_payment_evidence.

Resultado esperado:

```text
booking.status = pending_payment_evidence
payment.status = pending_evidence
price_snapshot = 180000
payer_plan_snapshot = Tarifa particular
```

### Escenario 2: reserva con Colsanitas Plan avanzado

1. Paciente dice que tiene medicina prepagada.
2. Bot pregunta entidad.
3. Paciente dice Colsanitas.
4. Bot pregunta plan.
5. Paciente dice Plan avanzado.
6. Sistema encuentra tarifa.
7. Crea cita.

Resultado esperado:

```text
payer_type_snapshot = Medicina prepagada
payer_snapshot = Colsanitas
payer_plan_snapshot = Plan avanzado
price_snapshot = 100000
```

### Escenario 3: plan no configurado

1. Paciente dice que tiene una entidad/plan no configurado.
2. Sistema no inventa precio.
3. Ofrece tarifa particular o revisión administrativa.

Resultado esperado:

```text
No booking confirmed with unknown price
```

### Escenario 4: no envía evidencia

1. Cita queda pending_payment_evidence.
2. Pasa el plazo.
3. No hay evidencia.

Resultado esperado:

```text
booking.status = expired_no_evidence
payment.status = expired_no_evidence
slot = released
```

### Escenario 5: evidencia enviada y admin no revisa

1. Paciente envía comprobante.
2. Pasa plazo de revisión.
3. Admin no revisa.

Resultado esperado:

```text
booking.status = pending_manual_payment_review or review_overdue
payment.status = review_overdue
slot = protected
alert = generated
```

No se libera slot por defecto.

### Escenario 6: admin aprueba transferencia

1. Evidencia enviada.
2. Admin aprueba con confirmed_against_bank=true.

Resultado esperado:

```text
payment.status = paid
booking.status = confirmed
audit_log created
```

### Escenario 7: respuesta negativa a recordatorio

1. Cita confirmada.
2. Recordatorio enviado 24 horas antes.
3. Paciente responde que no asistirá.
4. Sistema pide segunda confirmación.
5. Paciente confirma cancelación.

Resultado esperado:

```text
attendance_confirmation_status = declined_confirmed
booking.status = cancelled_by_patient
slot = released
refund.status = pending_review if paid
```

### Escenario 8: respuesta negativa sin segunda confirmación

1. Paciente responde que no asistirá.
2. No responde segunda confirmación.

Resultado esperado:

```text
booking is not cancelled immediately
attendance_confirmation_status = declined_pending_second_confirmation
```

### Escenario 9: cita virtual con link manual

1. Cita virtual confirmada.
2. Admin agrega link.
3. Sistema notifica al paciente.

Resultado esperado:

```text
booking_virtual_details.status = sent
provider = manual
```

### Escenario 10: agenda externa fake

1. Tenant usa provider fake externo.
2. Paciente selecciona slot.
3. Provider responde slot unavailable.

Resultado esperado:

```text
booking not confirmed
error = SLOT_NOT_AVAILABLE
```

## 8. Datos que no deben usarse

No usar:

- pacientes reales;
- números de documento reales;
- historias clínicas;
- diagnósticos;
- datos bancarios reales;
- comprobantes reales;
- secretos reales.

## 9. Seed inicial recomendado

Crear script futuro:

```text
scripts/seed_demo_data.py
```

Debe permitir:

```bash
python scripts/seed_demo_data.py --tenant psicologa-ana
python scripts/seed_demo_data.py --tenant clinica-vida
```

El script debe ser idempotente o tener modo reset controlado.

## 10. Fixtures de campañas y comunicados

### Campaña operativa MediChat

```text
name = Cierre por vacaciones
campaign_type = schedule_notice
message_type = operational
solution_code = medichat
audience_type = all_active_patients
channel = telegram
message = Este fin de semana no tendremos servicio por temporada de vacaciones. Retomaremos atención el martes.
```

Resultado esperado:

```text
campaign.status = sent or partially_sent
deliveries generated
marketing consent not required
audit events created
```

### Campaña marketing MediChat

```text
name = Promoción consulta inicial agosto
campaign_type = marketing
message_type = marketing
solution_code = medichat
audience_type = all_active_patients
channel = telegram
message = Durante agosto tendremos tarifa especial para consulta inicial.
```

Resultado esperado:

```text
recipients without allow_marketing are blocked_by_consent
deliveries only sent to allowed contacts
```

### Campaña programada

```text
send_mode = scheduled
scheduled_at = próximo viernes 08:00 America/Bogota
```

Resultado esperado:

```text
campaign.status = scheduled
no deliveries sent before scheduled_at
worker sends when due
```

## Escenario de cita virtual manual

Una sede `Teleconsulta` con `is_virtual = true` debe crear citas con `bookings.modality = virtual`, `room_id = null` y `virtual_link_status = pending` si aún no hay link. Al guardar una URL manual, el estado pasa a `created`; al marcar enviado, a `sent` con `virtual_link_sent_at`. `virtual_meeting_id` y `virtual_access_code` pueden acompañar la URL, pero sin `virtual_meeting_url` no crean ni envían el link.

### 3.12.3. Login administrativo real

Para Fase 6C.2, los tests de autenticación usan un usuario activo con password bcrypt en `public.users` y vínculo activo en `public.user_tenants` hacia un tenant activo. Los escenarios mínimos son: login exitoso, password incorrecto, usuario inactivo, ausencia de vínculos activos, `/api/auth/me` sin `schema_name`, rutas admin sin token, token inválido/expirado, tenant no asociado y ruta admin válida con token más `X-TotalChat-Tenant-Id`.

## Fase 6D.1 — Dashboard administrativo real

Los tests del dashboard usan un tenant administrativo autenticado con JWT y un contexto tenant-scoped. Los fixtures mínimos incluyen citas `scheduled` de hoy, futuras, virtuales con y sin `virtual_meeting_url`, intentos de pago `transfer` con `status = evidence_received` y evidencia recibida, además de servicios y profesionales activos/inactivos para validar conteos operativos sin exponer `schema_name`.


## 7. Fixtures IA Fase 7A.1

Las pruebas de providers deben usar fakes/mocks sin invocar OpenAI real. Un tenant demo puede tener documentos semánticos como políticas administrativas o descripciones de servicios, siempre almacenados en su schema tenant en `semantic_documents` con embeddings de dimensión `TOTALCHAT_EMBEDDING_DIMENSIONS`. Las pruebas deben verificar que `public.semantic_documents` no existe y que `schema_name` no se modela ni serializa.

En Fase 7A.1.1, los fakes capturan `base_url`, una API key ficticia, modelo y timeout sin red. Fixtures mínimos cubren OpenAI (`https://api.openai.com/v1`, `gpt-4o-mini`) y DeepInfra (`https://api.deepinfra.com/v1/openai`, `Qwen/Qwen3.6-35B-A3B`), precedencia de la key genérica y fallback legacy exclusivo de OpenAI. Para `reasoning_content` se prueban tres casos: exclusión por defecto, captura solo en metadata con `TOTALCHAT_LLM_CAPTURE_REASONING=true`, y respuesta sin ese atributo. En todos los casos `content` permanece como única respuesta visible y no existe persistencia ni red real. Nunca se usan tokens reales.
