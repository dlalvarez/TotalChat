# INTEGRATIONS_EXTERNAL_CALENDARS.md
# Integraciones Externas de Agenda, Calendarios y Reuniones Virtuales

## 1. Propósito

Este documento define la arquitectura de integración de TotalChat con agendas, calendarios y proveedores de reuniones virtuales externos.

La necesidad surge porque muchos médicos, especialistas, consultorios y clínicas ya utilizan sistemas externos para administrar su agenda. Un caso importante es Docplanner/Doctoralia, pero el diseño no debe limitarse a Docplanner. También deben poder integrarse Google Calendar, Microsoft 365/Outlook Calendar, Microsoft Teams/Graph y otros proveedores futuros.

El objetivo es evitar doble reserva sin sacrificar el alcance propio de TotalChat.

## 2. Decisión arquitectónica

TotalChat debe tener un motor interno de agenda y reservas, pero también debe soportar proveedores externos de agenda/calendario mediante una capa genérica de integración.

Docplanner, Google Calendar, Microsoft Calendar, Microsoft Teams y otros sistemas deben ser adaptadores intercambiables, no dependencias del core.

Regla rectora:

```text
TotalChat no debe depender de Docplanner, Google Calendar ni Microsoft para existir.
TotalChat debe poder integrarse con ellos cuando un tenant ya los use como autoridad de agenda o como proveedor de reuniones virtuales.
```

## 3. Diferencia fundamental: agenda vs reunión virtual

Es obligatorio separar dos conceptos:

```text
Agenda / calendario
  Maneja disponibilidad, ocupación, bloqueos, eventos, citas y prevención de doble reserva.

Reunión virtual
  Maneja creación, almacenamiento o envío de links de videollamada.
```

Aunque Google y Microsoft pueden cubrir ambos mundos, no deben mezclarse en el modelo.

Ejemplos:

```text
Google Calendar
- Puede consultar disponibilidad.
- Puede crear eventos.
- Puede bloquear espacios.
- Puede crear Google Meet si se configura.

Microsoft 365 / Outlook Calendar
- Puede consultar disponibilidad.
- Puede crear eventos.
- Puede bloquear agenda.
- Puede crear reuniones Teams mediante Microsoft Graph.

Microsoft Teams
- Es principalmente proveedor de reunión virtual.
- Normalmente se crea mediante evento de calendario Microsoft 365.

Docplanner / Doctoralia
- Es una agenda médica externa.
- Maneja slots, bookings, doctores, direcciones, servicios y callbacks.
- No reemplaza pagos, precios jerárquicos, conversación ni políticas de TotalChat.
```

Por tanto, TotalChat debe tener dos abstracciones principales:

```text
SchedulingProvider
MeetingProvider
```

## 4. SchedulingProvider

`SchedulingProvider` representa la fuente o autoridad usada para disponibilidad y reservas.

Implementaciones previstas:

```text
SchedulingProvider
├── InternalSchedulingProvider
├── DocplannerSchedulingProvider
├── GoogleCalendarSchedulingProvider
├── MicrosoftCalendarSchedulingProvider
└── OtherSchedulingProvider
```

### 4.1. Responsabilidades

Un `SchedulingProvider` debe exponer operaciones como:

```text
get_available_slots
create_booking
cancel_booking
reschedule_booking
get_booking
get_bookings
create_block
remove_block
sync_external_events
```

### 4.2. InternalSchedulingProvider

Es el proveedor por defecto.

TotalChat calcula disponibilidad, crea reservas, cancela, reprograma y mantiene su propia agenda usando PostgreSQL y su modelo interno.

### 4.3. DocplannerSchedulingProvider

Se usa cuando un tenant ya utiliza Docplanner/Doctoralia como agenda principal.

En este caso TotalChat debe:

- consultar disponibilidad en Docplanner;
- consultar bookings existentes;
- considerar breaks/bloqueos del calendario;
- crear la reserva externa antes de confirmar localmente;
- cancelar o mover la reserva externa cuando corresponda;
- guardar mapping entre booking local y booking externo;
- consumir callbacks o notificaciones externas;
- reconciliar cambios realizados directamente en Docplanner.

Docplanner no reemplaza:

- precios jerárquicos de TotalChat;
- pagos de TotalChat;
- revisión manual de transferencias;
- recordatorios propios;
- confirmación de asistencia propia;
- consola administrativa;
- multi-tenancy;
- conversación LangGraph;
- eventos hacia n8n.

### 4.4. GoogleCalendarSchedulingProvider

Se usa cuando la agenda real del profesional está en Google Calendar.

TotalChat debe poder:

- consultar eventos ocupados;
- crear eventos de reserva;
- cancelar eventos;
- reprogramar eventos;
- mapear profesionales con calendarios;
- mapear citas con eventos externos;
- evitar confirmar localmente si no pudo bloquear o crear el evento externo cuando Google Calendar sea autoridad.

Google Calendar puede actuar como autoridad externa de agenda o como calendario sincronizado.

### 4.5. MicrosoftCalendarSchedulingProvider

Se usa cuando la agenda real está en Microsoft 365 / Outlook Calendar.

TotalChat debe poder:

- consultar disponibilidad u ocupación;
- crear eventos;
- cancelar eventos;
- mover eventos;
- mapear profesionales con calendarios Microsoft;
- guardar external_event_id;
- opcionalmente combinarse con MicrosoftTeamsMeetingProvider para links virtuales.

### 4.6. OtherSchedulingProvider

Permite proveedores futuros sin romper el core.

Ejemplos futuros:

- Calendly.
- Doctoralia variantes regionales.
- Sistemas HIS/IPS.
- Software propio de clínicas.
- Agendas REST privadas.

## 5. MeetingProvider

`MeetingProvider` representa la creación, actualización, cancelación o almacenamiento de enlaces de reunión virtual.

Implementaciones previstas:

```text
MeetingProvider
├── ManualMeetingProvider
├── GoogleMeetProvider
├── MicrosoftTeamsMeetingProvider
├── ZoomMeetingProvider
└── OtherMeetingProvider
```

### 5.1. Responsabilidades

```text
create_meeting
update_meeting
cancel_meeting
get_meeting_link
```

### 5.2. ManualMeetingProvider

Proveedor inicial del MVP.

El administrador pega manualmente el link de la cita virtual en la consola.

TotalChat guarda el link en `booking_virtual_details` y puede enviarlo al paciente.

### 5.3. GoogleMeetProvider

Futuro proveedor para crear enlaces Google Meet, normalmente asociado a un evento de Google Calendar.

### 5.4. MicrosoftTeamsMeetingProvider

Futuro proveedor para crear reuniones Microsoft Teams mediante Microsoft Graph / Microsoft 365.

### 5.5. ZoomMeetingProvider

Proveedor futuro opcional.

## 6. Configuración por tenant

Cada tenant debe poder definir su estrategia de agenda y reunión virtual.

Ejemplos:

```text
Dra. Ana
schedule_authority = totalchat
meeting_provider = manual
```

```text
Dr. Carlos
schedule_authority = docplanner
meeting_provider = manual
```

```text
Clínica XYZ
schedule_authority = microsoft_calendar
meeting_provider = microsoft_teams
```

```text
Psicóloga Laura
schedule_authority = google_calendar
meeting_provider = google_meet
```

## 7. Modos de autoridad de agenda

TotalChat debe soportar al menos tres modos:

```text
internal_authoritative
external_authoritative
hybrid
```

### 7.1. internal_authoritative

TotalChat es la autoridad de agenda.

El proveedor externo puede no existir o puede recibir sincronización secundaria.

### 7.2. external_authoritative

El proveedor externo es la autoridad de agenda.

TotalChat no debe confirmar localmente hasta que el proveedor externo valide o cree la reserva.

### 7.3. hybrid

TotalChat y proveedor externo intercambian información.

Este modo es más complejo y debe implementarse con cuidado porque puede generar conflictos.

## 8. Modos de sincronización

Además de autoridad, se debe definir sincronización:

```text
none
read_only
write_through
bidirectional
```

### 8.1. none

No hay sincronización externa.

### 8.2. read_only

TotalChat consulta disponibilidad externa, pero no escribe.

Puede ser útil para evitar doble reserva, pero puede no ser suficiente para garantizar ocupación del slot.

### 8.3. write_through

TotalChat consulta y escribe en el proveedor externo antes de confirmar localmente.

Este es el modo recomendado cuando el proveedor externo es autoridad.

### 8.4. bidirectional

TotalChat escribe y también recibe cambios externos.

Debe incluir reconciliación, callbacks, sync runs y manejo de conflictos.

## 9. Regla crítica contra doble reserva

Para tenants con agenda externa como autoridad:

```text
TotalChat no debe confirmar la cita localmente hasta que el proveedor externo confirme, cree o bloquee el slot.
```

Ejemplo Docplanner:

```text
Paciente elige horario
↓
TotalChat llama DocplannerSchedulingProvider.create_booking
↓
Docplanner confirma booking
↓
TotalChat crea/actualiza booking local
↓
TotalChat guarda external_booking_mapping
↓
TotalChat continúa flujo de pago/confirmación según política
```

Ejemplo Google Calendar:

```text
Paciente elige horario
↓
TotalChat crea evento en Google Calendar
↓
Google responde OK
↓
TotalChat guarda external_event_id
↓
TotalChat confirma o mantiene hold según política de pago
```

Ejemplo Microsoft:

```text
Paciente elige horario
↓
TotalChat crea evento en Outlook Calendar
↓
Opcionalmente crea Teams meeting
↓
TotalChat guarda external_event_id y meeting_url
↓
TotalChat confirma o mantiene estado según pago
```

## 10. Flujo conversacional

El bot no debe conocer detalles de proveedores.

El bot llama herramientas genéricas:

```text
get_available_slots()
create_booking()
cancel_booking()
reschedule_booking()
```

El backend decide qué provider usar según configuración del tenant.

```text
Tenant usa agenda interna → InternalSchedulingProvider
Tenant usa Docplanner → DocplannerSchedulingProvider
Tenant usa Google → GoogleCalendarSchedulingProvider
Tenant usa Microsoft → MicrosoftCalendarSchedulingProvider
```

## 11. Modelo de datos propuesto

### 11.1. external_systems

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

### 11.2. scheduling_provider_configs

Define proveedor de agenda activo por tenant, organización o profesional según se requiera.

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

### 11.3. meeting_provider_configs

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

### 11.4. external_practitioner_mappings

Mapea profesionales internos contra recursos externos.

```text
id
practitioner_id
external_system_id
external_practitioner_id
raw_external_payload
status
last_synced_at
```

### 11.5. external_location_mappings

Mapea sedes, consultorios, direcciones o calendarios externos.

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

### 11.6. external_service_mappings

Mapea servicios internos con servicios externos.

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

### 11.7. external_booking_mappings

Mapea citas internas con reservas/eventos externos.

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

### 11.8. external_events

Registra eventos recibidos desde proveedores externos.

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

### 11.9. external_sync_runs

Registra ejecuciones de sincronización.

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

## 12. Ajustes a BookingService

BookingService no debe estar acoplado directamente al cálculo interno de disponibilidad.

Debe depender de una interfaz:

```python
class SchedulingProvider:
    def get_available_slots(self, request):
        ...

    def create_booking(self, request):
        ...

    def cancel_booking(self, request):
        ...

    def reschedule_booking(self, request):
        ...

    def get_booking(self, request):
        ...

    def sync_external_events(self, request):
        ...
```

En MVP se implementará:

```text
InternalSchedulingProvider
ManualMeetingProvider
```

Pero el contrato debe existir para no romper arquitectura después.

## 13. Relación con pagos

La agenda externa no reemplaza pagos TotalChat.

Incluso si Docplanner, Google o Microsoft crean/bloquean una reserva, TotalChat mantiene:

- pago simulado;
- transferencia;
- evidencia;
- revisión manual;
- Wompi futuro;
- estados internos de pago;
- políticas de expiración;
- reembolsos.

## 14. Relación con precios

La agenda externa no reemplaza el modelo de precios jerárquico.

TotalChat mantiene:

```text
payer_type → payer → payer_plan → practitioner_service_price
```

Si el proveedor externo tiene precios, pueden mapearse o consultarse, pero no deben limitar el modelo propio.

## 15. Relación con consola administrativa

La consola administrativa debe permitir configurar:

- proveedor de agenda;
- autoridad;
- modo de sincronización;
- credenciales o conexión;
- mapeos de profesionales;
- mapeos de sedes/calendarios;
- mapeos de servicios;
- errores de sincronización;
- eventos externos;
- reconciliación manual.

## 16. Relación con n8n

n8n puede participar como automatizador externo, pero no debe ser el motor de sincronización crítica.

Puede ayudar en:

- alertas de sync fallido;
- avisos de conflicto;
- notificaciones administrativas;
- recordatorios.

El estado y reconciliación deben vivir en TotalChat.

## 17. Roadmap recomendado

### Spec 011 — External Scheduling Provider Abstraction

Diseñar la capa genérica.

Incluye:

- SchedulingProvider.
- MeetingProvider.
- InternalSchedulingProvider.
- ManualMeetingProvider.
- external_systems.
- provider configs.
- mappings.
- provider fake/mock.
- tests.

### Spec 012 — Docplanner Scheduling Adapter

Implementar Docplanner como proveedor externo.

Incluye:

- credenciales;
- mapeo facility/doctor/address/service;
- slots;
- bookings;
- breaks;
- create/cancel/move booking;
- callbacks;
- reconciliación básica.

### Spec 013 — Google Calendar Scheduling Adapter

Implementar Google Calendar como proveedor de agenda.

Incluye:

- OAuth/service account según estrategia;
- calendar mapping;
- free/busy;
- create event;
- update event;
- cancel event;
- sync events;
- optional Google Meet.

### Spec 014 — Microsoft Calendar and Teams Adapter

Implementar Microsoft 365 / Outlook Calendar y Teams.

Incluye:

- Microsoft Graph;
- calendar mapping;
- create/update/cancel event;
- Teams meeting link;
- sync events;
- external mappings.

## 18. Impacto sobre MVP

No se implementarán Docplanner, Google Calendar ni Microsoft en MVP obligatorio.

Pero el MVP debe evitar acoplar BookingService de forma irreversible al motor interno.

MVP implementa:

```text
InternalSchedulingProvider
ManualMeetingProvider
```

Fases futuras implementan:

```text
DocplannerSchedulingProvider
GoogleCalendarSchedulingProvider
MicrosoftCalendarSchedulingProvider
GoogleMeetProvider
MicrosoftTeamsMeetingProvider
```

## 19. Regla final

```text
TotalChat debe poder operar de forma autónoma con agenda interna, pero también debe poder integrarse con agendas externas por tenant para evitar doble reserva. Docplanner, Google Calendar, Microsoft Calendar y Teams son adaptadores de una arquitectura extensible, no el core del producto.
```
