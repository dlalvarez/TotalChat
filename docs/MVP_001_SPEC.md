# MVP_001_SPEC.md  
# MVP 001 — Plataforma Base de Reservas Médicas Conversacionales

## 1. Objetivo

Construir una primera versión funcional de TotalChat que permita:

- Crear tenants.
- Administrar datos base.
- Configurar servicios, profesionales, precios y disponibilidad.
- Crear citas manuales.
- Crear citas conversacionales por Telegram.
- Manejar pagos simulados y transferencias con revisión manual.
- Manejar recordatorios y confirmación de asistencia.
- Soportar citas virtuales con link manual.

## 2. Incluye

- FastAPI backend.
- PostgreSQL.
- Schema por tenant.
- pgvector.
- Redis.
- Admin web.
- LangGraph agent.
- OpenAI provider.
- Telegram.
- Pagos simulados.
- Transferencia manual.
- Revisión administrativa.
- Recordatorios.
- Citas virtuales manuales.

## 3. No incluye

- Diagnóstico médico.
- Historia clínica.
- WhatsApp.
- Wompi productivo.
- Facturación electrónica.
- EPS integradas.
- Validación real de afiliación.
- Salas virtuales automáticas.
- Restaurantes.
- Hoteles.
- POS/carrito.

## 4. Historias principales

### H1 — Crear tenant

Como administrador de plataforma, quiero crear un tenant para que un profesional o clínica pueda operar aisladamente.

### H2 — Configurar servicios

Como administrador del tenant, quiero crear profesionales, servicios, modalidades y tarifas para que el bot pueda reservar.

### H3 — Configurar disponibilidad

Como administrador, quiero definir horarios y excepciones para que el sistema ofrezca slots válidos.

### H4 — Crear cita manual

Como staff, quiero crear una cita desde la consola para gestionar reservas no conversacionales.

### H5 — Crear cita conversacional

Como paciente, quiero reservar por Telegram conversando naturalmente.

### H6 — Transferencia con evidencia

Como paciente, quiero enviar comprobante de transferencia para que el consultorio revise mi pago.

### H7 — Revisión manual

Como administrador, quiero aprobar/rechazar pagos con evidencia.

### H8 — Recordatorio

Como paciente, quiero recibir recordatorio y confirmar asistencia.

### H9 — Cita virtual

Como administrador, quiero agregar link manual de cita virtual.

## 5. Criterios de aceptación

1. Se puede crear un tenant.
2. Se crea schema por tenant.
3. Se puede crear profesional.
4. Se puede crear servicio del profesional.
5. Se puede crear jerarquía comercial: payer_type, payer, payer_plan.
6. Se puede crear precio por service + payer_plan.
7. Se puede crear disponibilidad.
8. Se puede crear cita.
9. La cita guarda snapshot.
10. Se puede crear paciente mínimo.
11. Se puede reservar sin paciente previo.
12. Se puede recibir evidencia de transferencia.
13. Si no hay evidencia en tiempo, se libera slot.
14. Si hay evidencia, slot queda protegido.
15. Revisión vencida no libera automáticamente.
16. Admin puede aprobar pago.
17. Pago aprobado confirma cita.
18. Telegram puede completar un flujo básico.
19. Recordatorio permite confirmar asistencia.
20. Respuesta negativa requiere segunda confirmación.
21. Link virtual manual puede agregarse.
22. Aislamiento por tenant probado.
23. IA no inventa precio ni disponibilidad.

## Consideración arquitectónica — Proveedores externos de agenda

Aunque el MVP 001 no implementa Docplanner, Google Calendar ni Microsoft Calendar, el diseño del motor de agenda debe quedar preparado para una abstracción `SchedulingProvider`.

El MVP implementará:

```text
InternalSchedulingProvider
ManualMeetingProvider
```

Fuera del MVP 001:

- DocplannerSchedulingProvider.
- GoogleCalendarSchedulingProvider.
- MicrosoftCalendarSchedulingProvider.
- GoogleMeetProvider.
- MicrosoftTeamsMeetingProvider.
- Sincronización bidireccional externa.
- Reconciliación avanzada de conflictos.

Regla:

```text
BookingService no debe quedar acoplado irreversiblemente al motor interno. Debe poder delegar disponibilidad y reserva a un proveedor configurado en fases futuras.
```


## Criterios adicionales de implementación verificable

Además de los criterios funcionales del MVP, la implementación debe cumplir:

1. Los endpoints iniciales deben seguir `docs/API_CONTRACTS.md`.
2. Las transiciones de citas, pagos y asistencia deben seguir `docs/STATE_MACHINES.md`.
3. BookingService debe quedar preparado para `SchedulingProvider`.
4. El MVP implementa `InternalSchedulingProvider` y `ManualMeetingProvider`.
5. Las pruebas deben usar o inspirarse en `docs/TEST_FIXTURES.md`.
6. Todo PR debe revisarse contra `docs/PR_REVIEW_CHECKLIST.md`.

## Aclaración de naming del MVP

El MVP 001 corresponde al primer vertical de TotalChat:

```text
MediChat
```

Por tanto, cuando esta spec habla de pacientes, profesionales de salud, especialidades, planes, pólizas, EPS, prepagada y citas médicas, se refiere al dominio de MediChat.

TotalChat Platform aporta las capacidades comunes:

- multi-tenancy;
- auth;
- canales;
- conversaciones;
- LLMProvider;
- pagos;
- SchedulingProvider;
- MeetingProvider;
- notificaciones;
- auditoría.

Regla:

El MVP no debe implementar RestoChat, HotelChat, StayChat ni StoreChat. Solo debe dejar la estructura preparada para soluciones futuras.

## Consideración sobre campañas y comunicados

El MVP de MediChat debe dejar prevista la capacidad transversal de campañas y comunicados.

Una primera versión funcional puede implementarse después de las capacidades base de MediChat, pero el diseño del admin, contactos, pacientes, canales y preferencias debe permitir:

- enviar comunicados a pacientes;
- enviar campañas programadas;
- respetar preferencias;
- registrar entregas;
- medir resultados.

Regla:

Campañas no debe diseñarse como función aislada de MediChat, sino como módulo de TotalChat Platform.
