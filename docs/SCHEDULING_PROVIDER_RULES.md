# SCHEDULING_PROVIDER_RULES.md
# Reglas de proveedores de agenda, calendario y reuniones virtuales

## 1. Propósito

Este documento define cómo TotalChat debe manejar agenda interna, agendas externas, calendarios externos y proveedores de reuniones virtuales.

La meta es evitar doble reserva sin acoplar el producto a Docplanner, Google Calendar, Microsoft Calendar, Teams ni ningún proveedor específico.

## 2. Separación conceptual

TotalChat debe separar dos conceptos:

```text
SchedulingProvider = disponibilidad, slots, bloqueos, citas y eventos de agenda.
MeetingProvider = generación o administración de links de reuniones virtuales.
```

No mezclar agenda con reunión virtual.

## 3. SchedulingProvider

### 3.1. Responsabilidad

Un `SchedulingProvider` responde por:

- consultar disponibilidad;
- crear reserva;
- cancelar reserva;
- reprogramar reserva;
- crear bloqueos;
- eliminar bloqueos;
- consultar reservas externas si aplica;
- sincronizar eventos externos si aplica.

### 3.2. Implementaciones previstas

```text
InternalSchedulingProvider
DocplannerSchedulingProvider
GoogleCalendarSchedulingProvider
MicrosoftCalendarSchedulingProvider
OtherSchedulingProvider
```

### 3.3. Interfaz conceptual

```python
class SchedulingProvider:
    def get_available_slots(self, request): ...
    def create_booking(self, request): ...
    def cancel_booking(self, request): ...
    def reschedule_booking(self, request): ...
    def get_booking(self, request): ...
    def create_block(self, request): ...
    def remove_block(self, request): ...
    def sync_external_events(self, request): ...
```

### 3.4. Contrato interno de solo lectura (Fase 8A.10)

El backend resuelve el tenant y entrega una sesión ya contextualizada; ni el
cliente ni el request eligen `tenant_id` o `schema_name`. El request de slots
contiene `practitioner_service_id`, `date_from`, `date_to`, `modality` y filtros
opcionales de profesional, sede y consultorio. `InternalSchedulingProvider`
calcula desde reglas activas y vigentes, duración del servicio, modalidades,
excepciones activas y bookings bloqueantes. Los slots equivalentes se deduplican
por inicio, fin, profesional, sede, consultorio y modalidad.
Cuando se solicita consultorio, este debe existir, estar activo y pertenecer a la
sede solicitada; el backend rechaza cualquier inconsistencia antes de consultar
reglas o generar slots.

El rango es inclusivo y no puede superar 31 días. Como todavía no existe una
zona horaria tenant-scoped formal para las reglas recurrentes, el provider
conserva el patrón existente de horas locales sin offset; no infiere una zona.
Esta limitación debe resolverse en una fase documental y de datos autorizada
antes de presentar offsets como autoridad tenant-scoped.

La operación no crea reservas, holds o bloqueos y no se expone al LLM en esta
fase. `payer_plan_id` continúa aceptado únicamente por compatibilidad del
endpoint admin y no filtra slots ni precios.

## 4. MeetingProvider

### 4.1. Responsabilidad

Un `MeetingProvider` responde por:

- crear link de reunión;
- actualizar reunión;
- cancelar reunión;
- consultar link;
- guardar datos de acceso.

### 4.2. Implementaciones previstas

```text
ManualMeetingProvider
GoogleMeetProvider
MicrosoftTeamsMeetingProvider
ZoomMeetingProvider
OtherMeetingProvider
```

### 4.3. MVP

En MVP solo se implementa:

```text
ManualMeetingProvider
```

El administrador pega manualmente el link.

## 5. Modos de autoridad de agenda

### 5.1. internal_authoritative

TotalChat es autoridad de agenda.

Reglas:

- TotalChat calcula slots.
- TotalChat crea booking local.
- TotalChat controla bloqueos.
- No depende de proveedor externo.

Provider:

```text
InternalSchedulingProvider
```

### 5.2. external_authoritative

Un proveedor externo es autoridad.

Ejemplos:

- Docplanner.
- Google Calendar.
- Microsoft Calendar.

Reglas:

- TotalChat consulta disponibilidad externa.
- TotalChat crea reserva/bloqueo externo antes de confirmar localmente.
- TotalChat guarda mapping externo.
- TotalChat consume eventos externos si existen.
- Si falla proveedor externo, no confirmar localmente.
- Si proveedor externo cambia la cita, TotalChat debe sincronizar o marcar conflicto.

### 5.3. hybrid

TotalChat y proveedor externo coexisten.

Reglas:

- Requiere definición específica por spec.
- Debe manejar conflictos.
- No debe implementarse en MVP.
- Debe tener reconciliación administrativa.

## 6. Sync modes

```text
none
read_only
write_through
bidirectional
```

### 6.1. none

No hay sincronización externa.

### 6.2. read_only

TotalChat consulta proveedor externo para evitar conflictos, pero no crea eventos externos.

Riesgo: puede haber race condition si otro sistema reserva después de la consulta.

### 6.3. write_through

TotalChat escribe en proveedor externo cuando crea, cancela o reprograma.

Recomendado para `external_authoritative`.

### 6.4. bidirectional

TotalChat escribe y también recibe cambios externos.

Requiere callbacks, polling o sincronización programada.

## 7. Reglas anti doble reserva

1. Nunca confirmar cita local sin validar slot.
2. Si la autoridad es externa, validar/reservar externamente antes de confirmar local.
3. Si el provider externo retorna conflicto, mostrar otro horario.
4. Si se pierde conectividad con provider externo, no confirmar de forma optimista salvo política explícita.
5. Guardar `external_booking_mapping`.
6. Procesar eventos externos.
7. Marcar conflictos para revisión administrativa.

## 8. BookingService y SchedulingProvider

El `BookingService` no debe llamar directamente funciones internas de generación de slots.

Debe depender de una interfaz:

```text
SchedulingProvider
```

Flujo:

```text
BookingService
↓
SchedulingProviderRegistry
↓
Provider configurado por tenant/organización/profesional
↓
get_available_slots / create_booking / cancel_booking / reschedule_booking
```

## 9. Configuración por tenant

Cada tenant u organización puede tener configuración:

```text
provider_type
authority_mode
sync_mode
external_system_id
settings
```

Ejemplos:

### Tenant interno

```text
provider_type = internal
authority_mode = internal_authoritative
sync_mode = none
```

### Tenant Docplanner

```text
provider_type = docplanner
authority_mode = external_authoritative
sync_mode = bidirectional
```

### Tenant Google Calendar

```text
provider_type = google_calendar
authority_mode = external_authoritative
sync_mode = write_through
```

### Tenant Microsoft

```text
provider_type = microsoft_calendar
authority_mode = external_authoritative
sync_mode = write_through
meeting_provider = microsoft_teams
```

## 10. Regla para MVP

En MVP:

```text
SchedulingProvider = InternalSchedulingProvider
MeetingProvider = ManualMeetingProvider
```

Pero el código debe quedar diseñado para soportar otras implementaciones.

No implementar Docplanner/Google/Microsoft en MVP, salvo stubs o interfaces.

## 11. Docplanner como adaptador

Docplanner se tratará como un adaptador de `SchedulingProvider`.

No reemplaza:

- conversación;
- pagos;
- revisión manual de transferencias;
- precios jerárquicos;
- consola admin;
- recordatorios;
- confirmación de asistencia;
- n8n complementario;
- multi-tenancy.

## 12. Google Calendar como adaptador

Google Calendar puede actuar como agenda externa.

Debe manejar:

- eventos;
- bloqueos;
- disponibilidad;
- external_event_id;
- posible generación de Google Meet mediante MeetingProvider futuro.

## 13. Microsoft Calendar / Teams

Microsoft Calendar puede actuar como agenda externa mediante Microsoft Graph.

Microsoft Teams debe tratarse como MeetingProvider.

Una misma integración tecnológica puede implementar:

```text
MicrosoftCalendarSchedulingProvider
MicrosoftTeamsMeetingProvider
```

Pero las responsabilidades siguen separadas.

## 14. Reconciliación

Si un evento externo contradice una cita local:

```text
external_event = cancelled
local_booking = confirmed
```

Entonces:

- marcar `sync_conflict`;
- alertar admin;
- no sobrescribir silenciosamente si hay pago afectado;
- registrar external_event;
- registrar sync_run;
- esperar resolución administrativa si el impacto es crítico.

## 15. Pruebas obligatorias

Tests mínimos:

1. Internal provider retorna slots.
2. BookingService usa provider y no lógica directa.
3. Provider fake simula slot ocupado.
4. Provider fake simula error externo.
5. Si provider falla, no se confirma booking.
6. Si provider confirma, se crea mapping.
7. MeetingProvider manual guarda link.
8. MeetingProvider no se invoca para cita presencial.
