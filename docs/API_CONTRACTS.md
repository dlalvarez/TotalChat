# API_CONTRACTS.md
# Contratos API iniciales de TotalChat

## 1. Propósito

Este documento define los contratos REST iniciales que deben guiar la implementación de TotalChat.

La intención no es cerrar para siempre la API, sino evitar que Codex invente rutas, nombres, payloads y respuestas inconsistentes entre fases.

Los contratos aquí definidos deben usarse como base para:

- `specs/001-project-foundation/contracts.md`
- `specs/002-multitenancy/contracts.md`
- `specs/003-booking-domain/contracts.md`
- `specs/004-admin-console/contracts.md`
- `specs/007-payments-manual-review/contracts.md`
- `specs/008-reminders-confirmation/contracts.md`
- specs futuras de canales, agenda externa y reuniones virtuales.

## 2. Principios de diseño API

### 2.1. Separación por superficie

TotalChat debe separar superficies de API:

```text
/api/platform/*
/api/admin/*
/api/public/*
/api/webhooks/*
/api/internal/*
```

### 2.2. `/api/platform/*`

Rutas para administración SaaS/plataforma.

Ejemplos:

- crear tenant;
- listar tenants;
- provisionar schema;
- gestionar canales;
- gestionar usuarios globales.

Estas rutas no pertenecen a la operación diaria del tenant.

### 2.3. `/api/admin/*`

Rutas para consola administrativa del tenant.

Requieren autenticación de usuario administrativo y contexto de tenant.

Ejemplos:

- crear profesionales;
- crear servicios;
- definir precios;
- crear disponibilidad;
- revisar pagos;
- crear citas manuales.

### 2.4. `/api/public/*`

Rutas públicas controladas.

Ejemplos futuros:

- consulta pública de disponibilidad si se habilita;
- landing de reserva web;
- confirmaciones por token seguro.

### 2.5. `/api/webhooks/*`

Rutas de entrada desde sistemas externos.

Ejemplos:

- Telegram;
- WhatsApp futuro;
- Wompi futuro;
- Docplanner futuro;
- Google/Microsoft futuro;
- n8n si se recibe callback.

### 2.6. `/api/internal/*`

Rutas internas para workers, schedulers o n8n cuando aplique.

Deben protegerse con token interno o mecanismo equivalente.

## 3. Convenciones generales

### 3.1. Formato de respuesta exitosa

Respuesta simple:

```json
{
  "data": {}
}
```

Respuesta lista:

```json
{
  "data": [],
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total": 125
  }
}
```

Respuesta de acción:

```json
{
  "data": {
    "id": "uuid",
    "status": "created"
  }
}
```

### 3.2. Formato de error

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request payload.",
    "details": {}
  }
}
```

Códigos sugeridos:

```text
VALIDATION_ERROR
AUTHENTICATION_REQUIRED
AUTHORIZATION_FAILED
TENANT_NOT_FOUND
RESOURCE_NOT_FOUND
CONFLICT
BUSINESS_RULE_VIOLATION
EXTERNAL_PROVIDER_ERROR
PAYMENT_REVIEW_REQUIRED
SLOT_NOT_AVAILABLE
INTERNAL_ERROR
```

### 3.3. Identificadores

Usar UUID para entidades principales.

No exponer nombres de schemas al frontend ni al LLM.

### 3.4. Tenant context

Las rutas `/api/admin/*` deben resolver tenant por:

- token/sesión del usuario;
- header administrativo controlado;
- tenant seleccionado en la consola.

No se debe aceptar un `schema_name` enviado por el cliente.

Header opcional para consola multi-tenant:

```http
X-TotalChat-Tenant-Id: <tenant_uuid>
```

El backend debe verificar que el usuario tenga acceso al tenant.

### 3.5. Idempotencia

Para operaciones críticas se recomienda soportar:

```http
Idempotency-Key: <uuid>
```

Aplicar especialmente a:

- creación de cita;
- creación de intento de pago;
- aprobación de pago;
- eventos externos;
- webhooks.


### 3.6. Bootstrap administrativo pre-login

La Fase 6C.1.1 tampoco agrega contrato HTTP: el provisioning de tenants se ejecuta solo por CLI backend con `python3 -m app.tenancy.create_tenant` y escribe en `public.tenants` más el schema PostgreSQL del tenant. La Fase 6C.1 no agrega contrato HTTP. El bootstrap del primer usuario administrativo se ejecuta solo por CLI backend con `python3 -m app.auth.create_admin_user` y escribe en `public.users` y `public.user_tenants` después de validar `public.tenants`. Sigue pendiente el contrato de login real (`/api/auth/login` o equivalente), emisión de JWT, refresh tokens y protección completa de rutas admin.

## 4. Health y foundation

### 4.1. GET `/health`

Uso:

Validar que la app está viva.

Respuesta:

```json
{
  "data": {
    "status": "ok",
    "service": "totalchat-api",
    "version": "0.1.0"
  }
}
```

### 4.2. GET `/ready`

Uso:

Validar dependencias mínimas.

Respuesta:

```json
{
  "data": {
    "status": "ready",
    "database": "ok",
    "redis": "ok"
  }
}
```

## 5. Autenticación admin

### 5.1. POST `/api/auth/login`

Request:

```json
{
  "email": "admin@example.com",
  "password": "secret"
}
```

Response:

```json
{
  "data": {
    "access_token": "jwt",
    "refresh_token": "jwt",
    "token_type": "bearer",
    "expires_in": 1800
  }
}
```

### 5.2. POST `/api/auth/refresh`

Request:

```json
{
  "refresh_token": "jwt"
}
```

### 5.3. GET `/api/auth/me`

Response:

```json
{
  "data": {
    "id": "uuid",
    "email": "admin@example.com",
    "full_name": "Admin",
    "tenants": [
      {
        "tenant_id": "uuid",
        "tenant_name": "Consultorio Dra. Ana",
        "role": "owner"
      }
    ]
  }
}
```

## 6. Plataforma / tenants

### 6.1. POST `/api/platform/tenants`

Crea tenant y opcionalmente provisiona schema.

Request:

```json
{
  "name": "Consultorio Psicóloga Ana",
  "slug": "psicologa-ana",
  "owner_email": "ana@example.com",
  "owner_full_name": "Ana Gómez",
  "provision_schema": true
}
```

Response:

```json
{
  "data": {
    "id": "uuid",
    "name": "Consultorio Psicóloga Ana",
    "slug": "psicologa-ana",
    "status": "active",
    "schema_status": "provisioned"
  }
}
```

Reglas:

- `slug` debe ser único.
- `schema_name` lo genera el backend.
- No permitir que el usuario defina directamente el nombre del schema sin sanitización.
- Si falla el provisioning, registrar error y no dejar estado ambiguo.

### 6.2. GET `/api/platform/tenants`

Lista tenants.

### 6.3. GET `/api/platform/tenants/{tenant_id}`

Detalle tenant.

### 6.4. POST `/api/platform/tenants/{tenant_id}/channels`

Configura canal.

Request Telegram:

```json
{
  "channel_type": "telegram",
  "external_identifier": "telegram_bot_username_or_id",
  "settings": {
    "bot_name": "TotalChat Demo",
    "webhook_enabled": true
  }
}
```

Reglas:

- El token del bot no debe devolverse en respuestas.
- Secretos se guardan cifrados o en secret manager/variables según estrategia.

## 7. Organizaciones

### 7.1. POST `/api/admin/organizations`

Request:

```json
{
  "name": "Consultorio Psicóloga Ana",
  "organization_type": "independent_practitioner",
  "legal_name": "Ana Gómez",
  "tax_id": "123456789",
  "email": "contacto@example.com",
  "phone": "+573001112233"
}
```

Response:

```json
{
  "data": {
    "id": "uuid",
    "name": "Consultorio Psicóloga Ana",
    "status": "active"
  }
}
```

### 7.2. GET `/api/admin/organizations`

### 7.3. GET `/api/admin/organizations/{organization_id}`

### 7.4. PATCH `/api/admin/organizations/{organization_id}`

### 7.5. POST `/api/admin/organizations/{organization_id}/disable`

No eliminar físicamente por defecto.

## 8. Sedes y consultorios

### 8.1. POST `/api/admin/locations`

Request:

```json
{
  "organization_id": "uuid",
  "name": "Sede Poblado",
  "address": "Carrera 43A #...",
  "city": "Medellín",
  "neighborhood": "El Poblado",
  "reference": "Edificio Médico, piso 8",
  "is_virtual": false
}
```

### 8.2. POST `/api/admin/rooms`

Request:

```json
{
  "location_id": "uuid",
  "name": "Consultorio 801",
  "room_type": "consulting_room",
  "capacity": 1
}
```

## 9. Profesionales y especialidades

### 9.1. POST `/api/admin/practitioners`

Request:

```json
{
  "full_name": "Ana Gómez",
  "professional_type": "psychologist",
  "professional_license": "TP-12345",
  "email": "ana@example.com",
  "phone": "+573001112233"
}
```

### 9.2. POST `/api/admin/specialties`

Request:

```json
{
  "name": "Psicología",
  "description": "Servicios de psicología clínica y terapias."
}
```

### 9.3. POST `/api/admin/practitioners/{practitioner_id}/specialties`

Request:

```json
{
  "specialty_id": "uuid"
}
```

## 10. Servicios del profesional

### 10.1. POST `/api/admin/practitioner-services`

Request:

```json
{
  "organization_id": "uuid",
  "practitioner_id": "uuid",
  "service_catalog_id": null,
  "name": "Terapia cognitivo conductual",
  "description": "Sesión terapéutica individual de 60 minutos.",
  "duration_minutes": 60,
  "requires_payment": true
}
```

Reglas:

- El servicio pertenece al profesional.
- La especialidad no define precio.
- El precio no se guarda aquí como único precio.
- Debe permitir varios precios mediante `practitioner_service_prices`.

### 10.2. POST `/api/admin/practitioner-services/{service_id}/modalities`

Request presencial:

```json
{
  "modality": "in_person",
  "location_id": "uuid",
  "room_id": "uuid"
}
```

Request virtual:

```json
{
  "modality": "virtual",
  "location_id": null,
  "room_id": null
}
```

## 11. Jerarquía comercial y precios

### 11.1. POST `/api/admin/payer-types`

Request:

```json
{
  "code": "medicina_prepagada",
  "name": "Medicina prepagada",
  "description": "Planes de medicina prepagada."
}
```

### 11.2. POST `/api/admin/payers`

Request:

```json
{
  "payer_type_id": "uuid",
  "name": "Colsanitas",
  "description": "Entidad de medicina prepagada."
}
```

### 11.3. POST `/api/admin/payer-plans`

Request:

```json
{
  "payer_id": "uuid",
  "name": "Plan avanzado",
  "description": "Plan avanzado de Colsanitas."
}
```

### 11.4. POST `/api/admin/practitioner-service-prices`

Request:

```json
{
  "practitioner_service_id": "uuid",
  "payer_plan_id": "uuid",
  "price": 100000,
  "currency": "COP",
  "valid_from": "2026-07-01",
  "valid_to": null
}
```

Reglas:

- El precio se asocia a `service + payer_plan`.
- Particular se modela como `payer_type=particular`, `payer=Particular`, `payer_plan=Tarifa particular`.
- La cita debe guardar snapshot de tipo, pagador, plan y precio.

### 11.5. GET `/api/admin/practitioner-services/{service_id}/prices`

Debe devolver tarifas activas del servicio.

## 12. Pacientes

### 12.1. POST `/api/admin/patients`

Request mínimo:

```json
{
  "full_name": "Juan Pérez",
  "phone": "+573001112233",
  "email": null,
  "document_type": "CC",
  "document_number": "123456789"
}
```

`document_type` es opcional y puede ser `null`. Si se informa, debe pertenecer al catálogo controlado Colombia/MVP: `RC`, `TI`, `CC`, `PAS`, `CE`, `RE`, `PPT`, `SC`, `DNI`, `NIT`, `OTHER`.

Response:

```json
{
  "data": {
    "id": "uuid",
    "full_name": "Juan Pérez",
    "profile_status": "minimal"
  }
}
```

Reglas:

- Paciente previo no es requisito para cita.
- `full_name` es obligatorio; `phone`, `email`, `document_type` y `document_number` son opcionales.
- `created_from_channel` no se envía desde frontend ni clientes API; el backend lo asigna internamente como `admin`.
- El endpoint rechaza campos extra, incluido `schema_name`.
- Al crear desde consola, `profile_status` queda en `minimal` en Fase 6B.12.
- No se validan edad, nacionalidad, longitud/formato documental ni fuentes externas.

### 12.2. POST `/api/admin/patients/{patient_id}/payer-profiles`

Request:

```json
{
  "payer_plan_id": "uuid",
  "member_id": "ABC123",
  "validation_status": "declared",
  "valid_from": null,
  "valid_to": null
}
```

## 13. Disponibilidad

### 13.1. POST `/api/admin/availability-rules`

Request:

```json
{
  "organization_id": "uuid",
  "practitioner_id": "uuid",
  "practitioner_service_id": null,
  "location_id": "uuid",
  "room_id": "uuid",
  "modality": "in_person",
  "weekday": 0,
  "start_time": "08:00",
  "end_time": "12:00",
  "valid_from": "2026-07-01",
  "valid_to": null,
  "buffer_minutes": 0
}
```

Reglas:

- `weekday`: `0 = lunes` a `6 = domingo`, igual al contrato admin vigente.
- Si `practitioner_service_id` es null, aplica a servicios compatibles.
- La generación de slots debe respetar duración del servicio.

### 13.2. POST `/api/admin/availability-exceptions`

Request:

```json
{
  "practitioner_id": "uuid",
  "location_id": null,
  "room_id": null,
  "starts_at": "2026-07-20T08:00:00-05:00",
  "ends_at": "2026-07-20T12:00:00-05:00",
  "exception_type": "administrative_block",
  "reason": "Bloqueo administrativo"
}
```

### 13.3. GET `/api/admin/availability/slots`

Query:

```text
?practitioner_service_id=uuid
&practitioner_id=uuid
&modality=in_person
&date_from=2026-07-10
&date_to=2026-07-17
&payer_plan_id=uuid
&location_id=uuid
&room_id=uuid
```

Response:

```json
{
  "data": [
    {
      "starts_at": "2026-07-10T09:00:00-05:00",
      "ends_at": "2026-07-10T10:00:00-05:00",
      "practitioner_id": "uuid",
      "location_id": "uuid",
      "room_id": "uuid",
      "modality": "in_person",
      "source": "internal"
    }
  ]
}
```

Reglas:

- El endpoint debe usar `SchedulingProvider`.
- En MVP, provider implementado: `InternalSchedulingProvider`.
- No acoplar directamente el controller al cálculo interno.
- `availability_rules` es la fuente mínima de elegibilidad. Su `weekday` usa
  `0 = lunes` a `6 = domingo`, y su modalidad (`in_person`, `virtual` o `both`)
  decide la compatibilidad de la consulta.
- La ausencia de filas en `service_modalities` no elimina slots en Fase 8A.10;
  esa tabla no es un prerrequisito de la disponibilidad interna de solo lectura.
- `date_from` y `date_to` son inclusivos; el rango máximo es 31 días.
- `location_id`, si se informa, debe existir, estar activo y pertenecer a la
  organización del servicio del profesional. `room_id` requiere `location_id`,
  debe estar activo y pertenecer a esa sede. Las inconsistencias se rechazan
  antes de generar slots. La modalidad debe ser `in_person` o `virtual`.
- `payer_plan_id` se acepta por compatibilidad contractual, pero no filtra
  disponibilidad ni ejecuta lógica de precios en Fase 8A.10.
- Sin reglas elegibles se responde `{"data": []}`. Un rango inválido o demasiado
  amplio produce el error de dominio `VALIDATION_ERROR`.
- El endpoint admin puede devolver UUIDs operativos, pero nunca `schema_name`.

## 14. Citas

### 14.1. POST `/api/admin/bookings`

Request:

```json
{
  "patient": {
    "id": null,
    "full_name": "Juan Pérez",
    "phone": "+573001112233",
    "email": null
  },
  "practitioner_service_id": "uuid",
  "payer_plan_id": "uuid",
  "modality": "in_person",
  "starts_at": "2026-07-10T09:00:00-05:00",
  "location_id": "uuid",
  "room_id": "uuid",
  "created_channel": "admin"
}
```

Response:

```json
{
  "data": {
    "id": "uuid",
    "status": "tentative",
    "payment_status": "pending",
    "service_name_snapshot": "Terapia cognitivo conductual",
    "payer_plan_name_snapshot": "Plan avanzado",
    "price_snapshot": 100000,
    "currency_snapshot": "COP",
    "total_amount": 100000
  }
}
```

Reglas:

- Si paciente no existe, se crea mínimo.
- Debe validar slot con `SchedulingProvider`.
- Debe guardar snapshot.
- No confirmar si el pago es requerido y no hay pago confirmado o política que permita confirmación sin pago.

### 14.2. POST `/api/admin/bookings/{booking_id}/confirm`

Confirma cita según reglas de pago.

Request:

```json
{
  "reason": "Pago aprobado manualmente"
}
```

Reglas:

- No confirmar transferencia sin revisión aprobada.
- Si agenda externa es autoridad, debe existir booking externo/mapping válido.

### 14.3. POST `/api/admin/bookings/{booking_id}/cancel`

Request:

```json
{
  "reason": "Cancelado por paciente",
  "release_slot": true
}
```

### 14.4. POST `/api/admin/bookings/{booking_id}/reschedule`

Request:

```json
{
  "new_starts_at": "2026-07-11T10:00:00-05:00",
  "new_location_id": "uuid",
  "new_room_id": "uuid",
  "reason": "Solicitud paciente"
}
```

## 15. Pagos manuales/simulados

Estos contratos reflejan el baseline implementado para pagos manuales/simulados. No incluyen Wompi, pasarelas, tarjetas ni conciliación bancaria automática.

### 15.1. POST `/api/admin/payment-settings`

Request:

```json
{
  "organization_id": "uuid",
  "allow_transfer": true,
  "allow_simulated_payment": true,
  "allow_pay_on_site": false,
  "evidence_deadline_minutes": 60,
  "manual_review_deadline_minutes": 1440,
  "release_slot_on_missing_evidence": true,
  "release_slot_on_review_overdue": false,
  "status": "active"
}
```

Reglas:

- `organization_id` es obligatorio.
- `status` puede ser `active` o `inactive` y por defecto es `active`.
- Solo puede existir una fila `payment_settings` activa por organización.

### 15.2. GET `/api/admin/payment-settings`

Filtros soportados:

```text
organization_id
status
```

Response:

```json
{
  "data": [
    {
      "id": "uuid",
      "organization_id": "uuid",
      "allow_transfer": true,
      "allow_simulated_payment": true,
      "allow_pay_on_site": false,
      "evidence_deadline_minutes": 60,
      "manual_review_deadline_minutes": 1440,
      "release_slot_on_missing_evidence": true,
      "release_slot_on_review_overdue": false,
      "status": "active"
    }
  ]
}
```

### 15.3. PATCH `/api/admin/payment-settings/{payment_settings_id}`

Request: cualquiera de los campos configurables de `payment_settings` salvo su identificador.

Reglas:

- Cambiar configuración no reescribe historial de intentos de pago.
- `organization_id` no debe usarse para mover una configuración histórica entre organizaciones.
- `status` puede ser `active` o `inactive` y por defecto es `active` en creación.
- Solo puede existir una fila `payment_settings` activa por organización.
- `release_slot_on_review_overdue` debe permanecer `false` por defecto.

### 15.4. POST `/api/admin/payment-attempts`

Request transferencia:

```json
{
  "booking_id": "uuid",
  "method": "transfer",
  "amount": 100000,
  "currency": "COP"
}
```

Request pago simulado:

```json
{
  "booking_id": "uuid",
  "method": "simulated",
  "amount": 100000,
  "currency": "COP"
}
```

Request pago en sitio:

```json
{
  "booking_id": "uuid",
  "method": "pay_on_site",
  "amount": 100000,
  "currency": "COP"
}
```

`method` permitido:

```text
transfer
simulated
pay_on_site
```

`status` permitido:

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

Inicialización por método:

- `method=transfer` inicia en `evidence_required`.
- `method=simulated` inicia en `simulated_approved`.
- `method=pay_on_site` inicia en `pending` en el baseline backend actual.
- `under_review` y `cancelled` son estados implementados/reservados y no deben usarse en flujos nuevos salvo que la spec activa lo requiera.

Response transferencia:

```json
{
  "data": {
    "id": "uuid",
    "booking_id": "uuid",
    "method": "transfer",
    "status": "evidence_required",
    "amount": 100000,
    "currency": "COP",
    "expires_at": "2026-07-05T18:00:00-05:00"
  }
}
```

### 15.5. GET `/api/admin/payment-attempts`

Filtros sugeridos:

```text
booking_id
method
status
```

Uso: revisión administrativa, auditoría y seguimiento de intentos.

### 15.6. POST `/api/admin/payment-attempts/{payment_attempt_id}/evidence`

Request conceptual:

```json
{
  "storage_object_key": "payment-evidence/tenant/attempt/evidence.png",
  "original_filename": "evidence.png",
  "content_type": "image/png",
  "uploaded_channel": "admin",
  "notes": "Comprobante enviado por el paciente"
}
```

Reglas:

- Al registrar evidencia, el intento pasa a `evidence_received`.
- La cita pasa a revisión manual de pago según las reglas del dominio de reservas.
- El slot queda protegido.
- IA puede prevalidar o extraer datos, pero no aprobar.

### 15.7. POST `/api/admin/payment-attempts/{payment_attempt_id}/approve`

Request:

```json
{
  "notes": "Pago revisado y aprobado por administración."
}
```

Reglas:

- Solo una acción administrativa puede aprobar una transferencia.
- La aprobación pasa el intento a `approved`.
- Si pago requerido, puede confirmar la cita mediante servicios de dominio.
- La aprobación debe registrarse en `payment_reviews`.
- La IA no puede invocar esta aprobación como decisión propia.

### 15.8. POST `/api/admin/payment-attempts/{payment_attempt_id}/reject`

Request:

```json
{
  "notes": "El comprobante no corresponde al valor esperado."
}
```

Reglas:

- El rechazo pasa el intento a `rejected`.
- El rechazo debe registrarse en `payment_reviews`.
- Reintentos o cancelaciones posteriores deben pasar por servicios de dominio.

### 15.9. POST `/api/internal/payment-attempts/{payment_attempt_id}/expire-missing-evidence`

Uso: worker/scheduler interno expira un intento `transfer` que sigue sin evidencia después de `evidence_deadline_minutes`.

Reglas:

- Puede pasar el intento a `expired`.
- Libera slot solo si `release_slot_on_missing_evidence=true`.
- Debe protegerse con credenciales internas.

### 15.10. POST `/api/internal/payment-attempts/{payment_attempt_id}/mark-review-overdue`

Uso: worker/scheduler interno marca revisión vencida después de `manual_review_deadline_minutes`.

Reglas:

- No aprueba ni rechaza el pago.
- No libera slot por defecto.
- Libera slot solo si `release_slot_on_review_overdue=true`.
- Debe generar señal de alerta/escalamiento si existe automatización complementaria.

## 16. Citas virtuales

### 16.1. POST `/api/admin/bookings/{booking_id}/virtual-details`

Request link manual:

```json
{
  "provider": "manual",
  "meeting_url": "https://meet.example.com/abc",
  "meeting_id": null,
  "access_code": null,
  "created_mode": "manual"
}
```

Reglas:

- MVP soporta link manual.
- Providers automáticos son futuros.

## 17. Recordatorios y confirmación

### 17.1. GET `/api/admin/appointment-confirmation-settings`

### 17.2. PATCH `/api/admin/appointment-confirmation-settings`

Request:

```json
{
  "enabled": true,
  "reminder_hours_before": 24,
  "require_attendance_confirmation": true,
  "second_confirmation_on_negative_response": true,
  "no_response_policy": "notify_admin",
  "auto_cancel_on_no_response": false,
  "refund_policy_days": 5
}
```

### 17.3. POST `/api/internal/reminders/due`

Endpoint interno/scheduler para generar recordatorios vencidos.

### 17.4. POST `/api/admin/bookings/{booking_id}/attendance-confirmation`

Request confirmar:

```json
{
  "response": "confirmed",
  "channel": "telegram"
}
```

Request negativa inicial:

```json
{
  "response": "declined",
  "channel": "telegram"
}
```

Regla:

- `declined` no cancela inmediatamente.
- Debe pasar a `declined_pending_second_confirmation`.

### 17.5. POST `/api/admin/bookings/{booking_id}/attendance-cancellation-confirmation`

Request:

```json
{
  "confirm_cancel": true
}
```

Reglas:

- Solo después de segunda confirmación se cancela y libera slot.
- Si había pago, crear/actualizar estado de reembolso según política.

## 18. Webhooks

### 18.1. POST `/api/webhooks/telegram/{channel_token}`

Recibe mensajes Telegram.

Reglas:

- Resolver tenant por `channel_token` o configuración segura.
- Persistir mensaje.
- Invocar agente.
- Responder por Telegram.
- No exponer errores internos al usuario.

### 18.2. POST `/api/webhooks/wompi`

Futuro.

### 18.3. POST `/api/webhooks/external-scheduling/{provider}`

Futuro para Docplanner/Google/Microsoft cuando aplique.

## 19. Contratos de proveedores internos

Los endpoints de disponibilidad y bookings no deben implementar directamente la lógica de agenda. Deben usar servicios que dependan de interfaces:

```text
SchedulingProvider
MeetingProvider
LLMProvider
EmbeddingsProvider
PaymentProvider
```

En MVP:

```text
SchedulingProvider = InternalSchedulingProvider
MeetingProvider = ManualMeetingProvider
PaymentProvider = SimulatedPaymentProvider / ManualTransferProvider
LLMProvider = OpenAICompatibleProvider (OpenAI o DeepInfra por configuración)
```

La Fase 7A.1.1 no agrega endpoints HTTP. El contrato interno normaliza completions como `LLMResponse(content, model, provider, metadata)` usando solo `choices[0].message.content` como contenido visible. `reasoning_content` no forma parte de `content`, no se expone por HTTP, UI o canales y no se guarda ni registra por defecto; solo puede capturarse como metadata interna con `TOTALCHAT_LLM_CAPTURE_REASONING=true`. Ninguna lógica de negocio, tool, pago, cita, disponibilidad, autorización o tenant puede depender de esa metadata. La selección del adaptador usa configuración genérica y no ocurre en LangGraph, canales ni dominio.

OpenAI, DeepInfra/Qwen, Kimi futuro y cualquier proveedor OpenAI-compatible reciben su credencial LLM exclusivamente desde `TOTALCHAT_LLM_API_KEY`; no existe fallback a variables específicas de proveedor.

OpenAI no tiene una clase concreta propia: al igual que DeepInfra/Qwen y Kimi futuro, es una configuración de `OpenAICompatibleProvider`. Los consumidores usan exclusivamente `LLMProvider`/`EmbeddingsProvider` y las factories internas.

LLM y embeddings pueden seleccionar proveedores distintos. El ejemplo MVP usa DeepInfra/Qwen para LLM y OpenAI `text-embedding-3-small` con dimensión 1536 para embeddings. Un cambio a un modelo de embeddings DeepInfra/Qwen requiere validar su dimensión real frente a `semantic_documents.embedding VECTOR(...)` y `TOTALCHAT_EMBEDDING_DIMENSIONS` antes de persistir vectores.

## 20. Endpoints mínimos por fase

### Fase 1

- GET `/health`
- GET `/ready`

### Fase 2

- POST `/api/platform/tenants`
- GET `/api/platform/tenants`
- POST `/api/platform/tenants/{tenant_id}/channels`

### Fase 3

- CRUD organizaciones
- CRUD sedes
- CRUD consultorios
- CRUD profesionales
- CRUD especialidades
- CRUD servicios
- CRUD precios
- CRUD pacientes

### Fase 4

- Disponibilidad
- Crear cita
- Cancelar cita
- Reprogramar cita

### Fase 5

- Configuración pagos
- Intentos de pago
- Evidencias
- Revisiones

### Fase 6

- Endpoints requeridos por consola admin

### Fase 7+

- Agent tools internas
- Telegram webhook
- Recordatorios
- Integraciones externas futuras

## 21. Campañas y comunicados

### 21.1. POST `/api/admin/campaigns`

Crea campaña.

### 21.2. GET `/api/admin/campaigns`

Lista campañas.

### 21.3. POST `/api/admin/campaigns/{campaign_id}/preview-audience`

Calcula audiencia estimada.

### 21.4. POST `/api/admin/campaigns/{campaign_id}/send-now`

Envía inmediatamente.

Request:

```json
{
  "confirm_send": true
}
```

### 21.5. POST `/api/admin/campaigns/{campaign_id}/schedule`

Programa envío.

### 21.6. POST `/api/admin/campaigns/{campaign_id}/cancel`

Cancela campaña.

### 21.7. GET `/api/admin/campaigns/{campaign_id}/deliveries`

Lista entregas.

### 21.8. GET `/api/admin/campaigns/{campaign_id}/metrics`

Métricas.

## Fase 6B.4 — Especialidades y consultorios

Endpoints administrativos tenant-scoped agregados o completados:

- `GET /api/admin/specialties`: lista especialidades con orden determinista.
- `POST /api/admin/specialties`: crea una especialidad tenant-scoped, rechaza campos extra y nombres duplicados normalizados por espacios/case.
- `GET /api/admin/specialties/{specialty_id}`: consulta una especialidad del tenant actual.
- `PATCH /api/admin/specialties/{specialty_id}`: edita nombre, descripción o estado (`active`/`inactive`).
- `POST /api/admin/specialties/{specialty_id}/disable`: inactiva reversiblemente la especialidad maestra.
- `GET /api/admin/practitioners/{practitioner_id}/specialties`: lista relaciones profesional-especialidad e incluye identificador interno, nombre legible, estado de relación y estado de especialidad.
- `POST /api/admin/practitioners/{practitioner_id}/specialties`: asigna o reactiva una especialidad activa sin duplicar la relación.
- `PUT /api/admin/practitioners/{practitioner_id}/specialties`: sincroniza transaccionalmente el conjunto completo de especialidades activas; valida el profesional, rechaza IDs duplicados o especialidades inactivas/inexistentes, crea/reactiva relaciones necesarias e inactiva las retiradas sin borrado físico.
- `POST /api/admin/practitioners/{practitioner_id}/specialties/{specialty_id}/disable`: retira reversiblemente una asignación.

`room_type` en `POST/PATCH /api/admin/rooms` acepta únicamente: `consulta_general`, `procedimientos`, `terapia`, `diagnostico`, `virtual`, `otro` o `null` cuando el campo queda vacío para compatibilidad de datos existentes.

## Fase 6B.5 — Organization practitioners admin API

Endpoints tenant-scoped bajo `/api/admin`:

- `GET /api/admin/organization-practitioners`
  - Filtros opcionales: `organization_id`, `practitioner_id`, `status`, `include_inactive`.
  - Devuelve nombres y estados legibles de organización y profesional; no devuelve `schema_name`.
- `POST /api/admin/organization-practitioners`
  - Payload: `organization_id`, `practitioner_id`, `role` opcional (`member` por defecto).
  - Crea activa, reactiva si estaba inactiva y evita duplicados.
  - Rechaza padres inexistentes o inactivos para nuevas relaciones.
- `PATCH /api/admin/organizations/{organization_id}/practitioners/{practitioner_id}`
  - Permite cambiar `role` y `status`.
  - No permite cambiar IDs de la pareja.
- `POST /api/admin/organizations/{organization_id}/practitioners/{practitioner_id}/disable`
  - Inactiva la relación sin borrar físicamente ni tocar organización, profesional, especialidades o servicios.

Respuesta de relación:

```json
{
  "organization_id": "uuid",
  "organization_name": "Clínica Vida",
  "organization_status": "active",
  "practitioner_id": "uuid",
  "practitioner_name": "Dra. Ana Pérez",
  "practitioner_status": "active",
  "role": "member",
  "status": "active"
}
```


### Fase 6B.6 — CRUD administrativo de servicios del profesional

`PractitionerService` se administra con `GET /api/admin/practitioner-services`, `POST /api/admin/practitioner-services`, `GET /api/admin/practitioner-services/{service_id}`, `PATCH /api/admin/practitioner-services/{service_id}` y `POST /api/admin/practitioner-services/{service_id}/disable`. Crear y reactivar servicios exige organización activa, profesional activo y relación `organization_practitioners` activa para la pareja `organization_id + practitioner_id`. El listado conserva servicios históricos aunque los padres o la relación estén inactivos, e incluye nombres y estados legibles. No expone `schema_name`.

Campos de creación: `organization_id`, `practitioner_id`, `name`, `description`, `duration_minutes`, `requires_payment`. Edición solo permite `name`, `description`, `duration_minutes`, `requires_payment`, `status`; no permite cambiar organización ni profesional. La duplicidad se valida en aplicación por organización + profesional + nombre normalizado case-insensitive; no resuelve carreras concurrentes extremas.

Servicios no incluye precios todavía. Servicios no incluye modalidades todavía en la consola administrativa. Servicios no incluye disponibilidad todavía.


## Fase 6B.7 — Admin pagadores y planes

La superficie `/api/admin` expone CRUD lógico para `payer-types`, `payers` y `payer-plans`. Los endpoints listan históricos por defecto, soportan filtros `status`/`include_inactive` y devuelven nombres legibles de relaciones para evitar que la consola muestre UUIDs. Esta fase excluye precios y tarifas.

## Fase 6B.8 — Admin service prices

Endpoints bajo `/api/admin`:

- `GET /practitioner-service-prices`: listado general con filtros opcionales `organization_id`, `practitioner_id`, `practitioner_service_id`, `payer_type_id`, `payer_id`, `payer_plan_id`, `status`, `include_inactive`.
- `GET /practitioner-service-prices/{price_id}`: detalle de precio.
- `POST /practitioner-service-prices`: crea precio activo por defecto con `practitioner_service_id`, `payer_plan_id`, `price`, `currency`, `valid_from`, `valid_to`.
- `PATCH /practitioner-service-prices/{price_id}`: permite `price`, `currency`, `valid_from`, `valid_to`, `status`; no permite cambiar servicio ni plan.
- `POST /practitioner-service-prices/{price_id}/disable`: inactiva sin borrado físico.
- `GET /practitioner-services/{service_id}/prices`: se mantiene por compatibilidad y devuelve datos legibles enriquecidos.

Las respuestas incluyen nombres y estados legibles para servicio, organización, profesional, plan, pagador y tipo de pagador. Crear o reactivar requiere servicio, plan, pagador y tipo activos. No se permiten precios negativos, moneda distinta a código ISO de 3 letras mayúsculas, `valid_to < valid_from`, duplicado por servicio + plan + `valid_from`, ni solapamiento entre vigencias activas del mismo servicio y plan. `valid_to = null` representa vigencia abierta.

La API conserva el campo `currency`, pero la consola de Fase 6B.8 envía COP automáticamente y no permite editar moneda. La moneda operativa por tenant y `default_currency` quedan para una fase futura de Configuración; no se implementa multi-moneda ni conversión.

## 12. Disponibilidad base administrativa

`/api/admin/practitioner-availability-rules` administra reglas recurrentes de disponibilidad base. Soporta listado, detalle, creación, edición lógica e inactivación mediante:

- `GET /api/admin/practitioner-availability-rules`
- `GET /api/admin/practitioner-availability-rules/{rule_id}`
- `POST /api/admin/practitioner-availability-rules`
- `PATCH /api/admin/practitioner-availability-rules/{rule_id}`
- `POST /api/admin/practitioner-availability-rules/{rule_id}/disable`

El payload usa `day_of_week` con `0 = Monday/Lunes` y `6 = Sunday/Domingo`, `start_time < end_time`, `valid_from` requerido y `valid_to` opcional. Crear o reactivar exige organización, profesional, relación organización-profesional y servicio opcional activos. No expone `schema_name`.

### Fase 6B.9.1 — Bloqueos e indisponibilidad

La disponibilidad base define elegibilidad de atención. Los bloqueos/indisponibilidades reducen esa elegibilidad para rangos futuros donde un profesional no puede atender, aunque sus reglas recurrentes indiquen que normalmente podría hacerlo. Las reservas, citas y holds serán los registros que ocupen realmente un horario en fases posteriores; esta fase no calcula slots, no crea citas y no crea reservas.

La consola administra bloqueos con profesional, sede opcional, consultorio opcional, inicio, fin, tipo controlado por backend, motivo opcional y estado activo/inactivo. No hay borrado físico. Los tipos de bloqueo del MVP son controlados para preservar semántica operativa y facilitar reglas futuras; la configuración dinámica por tenant queda como mejora futura.

#### Endpoints admin de bloqueos

`/api/admin/availability-exceptions` soporta `GET`, `POST`, `GET /{exception_id}`, `PATCH /{exception_id}` y `POST /{exception_id}/disable`. El listado permite filtrar por `practitioner_id`, `location_id`, `room_id`, `exception_type`, `status`, `include_inactive`, `starts_from` y `starts_to`.

Tipos permitidos: `vacation`, `medical_leave`, `personal`, `meeting`, `lunch`, `training`, `maintenance`, `temporary_closure`, `administrative`, `other`.

Las respuestas incluyen IDs internos para operación del frontend y nombres/estados legibles: profesional, sede, organización y consultorio, además de `exception_type_label`; no exponen `schema_name`.

## Fase 6B.10 — Admin appointments

Endpoints tenant-scoped bajo `/api/admin`:

- `GET /appointments` con filtros `organization_id`, `location_id`, `room_id`, `practitioner_id`, `practitioner_service_id`, `patient_id`, `status`, `date`, `date_from`, `date_to`.
- `GET /appointments/{appointment_id}`.
- `POST /appointments`.
- `PATCH /appointments/{appointment_id}` limitado en esta fase a `notes` y `status`.
- `POST /appointments/{appointment_id}/cancel` → `cancelled`.
- `POST /appointments/{appointment_id}/complete` → `completed`.
- `POST /appointments/{appointment_id}/no-show` → `no_show`.

Estados administrativos: `scheduled`, `cancelled`, `completed`, `no_show`. Solo `scheduled` ocupa horario para validaciones de conflicto. Las respuestas incluyen nombres legibles para organización, sede, consultorio, profesional, servicio y paciente, y no exponen `schema_name`.

`date_to` se interpreta inclusivo hasta el final del día indicado para mantener consistencia con los listados administrativos existentes.

## Fase 6B.11 — Pagos administrativos base

Endpoints funcionales de consola: `GET /api/admin/payments`, `GET /api/admin/payments/{payment_attempt_id}`, `POST /api/admin/payments/{payment_attempt_id}/approve` y `POST /api/admin/payments/{payment_attempt_id}/reject`.

El listado acepta filtros por `organization_id`, `status`, `method`, `date_from`, `date_to`, `patient`, `booking_id` y `practitioner_id`. Las respuestas incluyen nombres legibles de paciente, profesional, servicio, organización, sede y consultorio cuando existen; no exponen `schema_name`.

La aprobación/rechazo manual de esta superficie aplica únicamente a intentos `transfer` en estado `evidence_received` y debe ejecutarse mediante `PaymentReviewService`. La aprobación crea `payment_reviews.decision = approved`, actualiza `payment_attempts.status = approved`, `payment_attempts.reviewed_at`, `payment_attempts.reviewed_by_user_id` cuando exista y `bookings.payment_status = paid`. El rechazo requiere `reason` o `notes`, crea `payment_reviews.decision = rejected`, actualiza `payment_attempts.status = rejected`, `payment_attempts.reviewed_at`, `payment_attempts.reviewed_by_user_id` cuando exista y `bookings.payment_status = rejected`. Ninguna acción confirma, cancela o libera automáticamente la cita.

## Pacientes administrativos — Fase 6B.12

Endpoints tenant-scoped bajo `/api/admin`:

- `GET /patients`: lista pacientes activos e inactivos. Filtros opcionales: `q` por nombre/documento/teléfono/email y `profile_status`.
- `GET /patients/{patient_id}`: devuelve detalle básico o `404` si no existe.
- `POST /patients`: crea paciente con `full_name` obligatorio y campos opcionales `phone`, `email`, `document_type`, `document_number`. Rechaza campos extra y `schema_name`; asigna `created_from_channel = admin` y `profile_status = minimal`. `document_type`, si se informa, se normaliza a mayúsculas y debe pertenecer al catálogo Colombia/MVP `RC`, `TI`, `CC`, `PAS`, `CE`, `RE`, `PPT`, `SC`, `DNI`, `NIT`, `OTHER`.
- `PATCH /patients/{patient_id}`: edita datos administrativos básicos y `profile_status`; valida estados `minimal`, `incomplete`, `complete`, `verified`, `inactive`. `document_type` puede ser `null` o un valor del catálogo Colombia/MVP `RC`, `TI`, `CC`, `PAS`, `CE`, `RE`, `PPT`, `SC`, `DNI`, `NIT`, `OTHER`.
- `POST /patients/{patient_id}/disable`: inactiva lógicamente con `profile_status = inactive`; es idempotente y no elimina relaciones ni citas.

La serialización de paciente incluye `id`, datos administrativos básicos, `profile_status`, `created_from_channel`, `created_at` y `updated_at`. No incluye `schema_name` ni información interna del tenant.

## Admin appointments — modalidad derivada por sede

En `POST /api/admin/appointments`, `location_id` es obligatorio y `modality` no forma parte del contrato externo. El backend deriva `bookings.modality` desde `locations.is_virtual` (`virtual` para sedes virtuales, `in_person` para sedes presenciales). Las sedes virtuales rechazan `room_id`; las sedes presenciales rechazan datos de link virtual.

Los links virtuales MVP son manuales y se guardan en columnas de `bookings`, no en tabla separada. Sin `virtual_meeting_url`, una cita virtual responde `virtual_link_status = pending`; `virtual_meeting_id` y `virtual_access_code` son auxiliares y no bastan por sí solos para considerar creado/enviado el link. Con URL manual, el estado es `created`; marcar enviado exige URL, pasa a `sent` y completa `virtual_link_sent_at`; al cancelar con URL existente, pasa a `cancelled`. Las citas presenciales responden `virtual_link_status = not_applicable`.

### 5.3. Fase 6C.2 — Login administrativo real

`POST /api/auth/login` autentica usuarios existentes en `public.users` con password bcrypt y exige usuario activo, al menos un vínculo activo en `public.user_tenants` y tenant activo. La respuesta MVP entrega solo access token JWT bearer por 30 minutos:

```json
{
  "data": {
    "access_token": "jwt",
    "token_type": "bearer",
    "expires_in": 1800
  }
}
```

`GET /api/auth/me` requiere `Authorization: Bearer <token>` y devuelve el usuario más tenants disponibles con `tenant_id`, `tenant_name`, `tenant_slug` y `role`. Nunca devuelve `schema_name` ni `password_hash`.

Las rutas `/api/admin/*` requieren ambos headers:

```http
Authorization: Bearer <token>
X-TotalChat-Tenant-Id: <tenant_uuid>
```

El backend valida pertenencia activa del usuario al tenant seleccionado y resuelve internamente el schema tenant para `SET LOCAL search_path`. El frontend no envía ni recibe `schema_name`. `POST /api/auth/refresh` queda diferido para Fase 6C.3 para mantener acotado este PR.

### 5.3.1. Fase 6D.1 — Dashboard administrativo real

`GET /api/admin/dashboard/summary` devuelve un resumen operativo real del tenant seleccionado. Requiere `Authorization: Bearer <token>` y `X-TotalChat-Tenant-Id`; el backend valida pertenencia activa del usuario al tenant y usa el contexto tenant-scoped existente. La ruta no acepta ni devuelve `schema_name`.

Respuesta:

```json
{
  "data": {
    "metrics": {
      "appointments_today": 0,
      "upcoming_appointments": 0,
      "appointments_pending_payment": 0,
      "payment_reviews_pending": 0,
      "virtual_appointments_without_link": 0,
      "active_services": 0,
      "active_practitioners": 0
    },
    "today_appointments": [],
    "pending_payment_reviews": [],
    "virtual_link_alerts": []
  }
}
```

`appointments_today` cuenta citas del día actual completo. `upcoming_appointments` cuenta únicamente citas `scheduled` futuras con `starts_at > now`; no incluye citas pasadas del mismo día.

Las listas usan nombres legibles de paciente, profesional, servicio y sede. Los UUIDs viajan solo como identificadores internos para navegación o keys del frontend, no como experiencia principal administrativa. No incluye recordatorios, confirmación de asistencia, Telegram, LangGraph, Wompi, WhatsApp, campañas ni configuración de bot.


## 14. Fase 7A.1 — sin endpoints HTTP

La Fase 7A.1 no agrega contratos HTTP. Solo introduce providers IA backend y la tabla tenant-scoped `semantic_documents`. Ninguna ruta admin, pública, webhook, interna o de frontend debe exponer `schema_name` ni permitir que el cliente o el LLM seleccione el schema tenant.
