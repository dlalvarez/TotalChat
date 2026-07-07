# ROADMAP.md  
# Roadmap de TotalChat

## Fase 0 — Gobierno documental y SDD

Objetivo: preparar la base documental.

Entregables:

- README.md.
- CONSTITUTION.md.
- ARCHITECTURE.md.
- DATA_MODEL.md.
- AI_BOUNDARIES.md.
- SECURITY.md.
- DECISIONS.md.
- MVP_001_SPEC.md.
- SDD_SPECKIT_GUIDE.md.

## Fase 1 — Fundación técnica

Objetivo: crear base del proyecto.

Entregables:

- FastAPI.
- React/Vite admin base.
- Docker Compose.
- PostgreSQL.
- pgvector.
- Redis.
- Healthcheck.
- Configuración.
- Logging.
- Tests básicos.

## Fase 2 — Multi-tenancy

Objetivo: implementar schema por tenant.

Entregables:

- public.tenants.
- public.tenant_channels.
- public.users.
- user_tenants.
- TenantResolver.
- TenantProvisioningService.
- Migraciones por schema.
- Tests de aislamiento.

## Fase 3 — Dominio de reservas

Objetivo: implementar modelo médico/reservas.

Entregables:

- Organizaciones.
- Sedes.
- Consultorios.
- Profesionales.
- Especialidades.
- Servicios del profesional.
- Modalidades.
- Precios por payer plan.
- Pacientes mínimos.

## Fase 4 — Agenda y citas

Objetivo: implementar disponibilidad y reservas sin IA.

Entregables:

- availability_rules.
- availability_exceptions.
- slot generation.
- create_tentative_booking.
- confirm_booking.
- cancel_booking.
- reschedule_booking.
- snapshots.

## Fase 5 — Pagos manuales/simulados

Objetivo: manejar pagos sin pasarela real.

Entregables:

- payment_settings.
- payment_attempts.
- payment_evidence.
- payment_reviews.
- Transferencia.
- Pago simulado.
- Pago en sitio configurable.
- Vencimiento por no evidencia.
- Revisión vencida sin liberar slot.

## Fase 6 — Consola administrativa MVP

Objetivo: permitir autogestión de datos.

Entregables:

- Login.
- Dashboard.
- CRUD organizaciones.
- CRUD sedes.
- CRUD consultorios.
- CRUD profesionales.
- CRUD especialidades.
- CRUD servicios.
- Tarifas.
- Disponibilidad.
- Citas.
- Pagos.
- Links virtuales.

## Fase 7 — LangGraph Booking Agent

Objetivo: agente conversacional.

Entregables:

- LLMProvider.
- OpenAIProvider.
- EmbeddingsProvider.
- Graph.
- Tools.
- Conversation state.
- Conversaciones simuladas.

## Fase 8 — Telegram

Objetivo: primer canal real.

Entregables:

- Telegram bot.
- Webhook.
- Resolver tenant por canal.
- Persistencia de mensajes.
- Envío de respuestas.

## Fase 9 — Recordatorios y confirmación

Objetivo: reducir no-show.

Entregables:

- reminder settings.
- attendance confirmation.
- negative response second confirmation.
- no-response policy.
- eventos para n8n.

## Fase 10 — Citas virtuales

Objetivo: links manuales.

Entregables:

- booking_virtual_details.
- Agregar link desde admin.
- Notificar link al paciente.
- Alertas de link pendiente.

## Fase 11 — Wompi sandbox

Objetivo: pasarela real en pruebas.

Entregables:

- Crear link.
- Webhook.
- Validación.
- Confirmar pago.
- Confirmar cita.

## Fase 12 — WhatsApp

Objetivo: canal comercial futuro.

Entregables:

- Webhook WhatsApp.
- Resolver tenant por número.
- Enviar/recibir mensajes.
- Plantillas si aplica.

## Fase 13 — n8n complementario

Objetivo: automatizaciones externas.

Entregables:

- Domain events.
- Webhooks salientes.
- Recordatorios.
- Alertas.
- Encuestas.

## Fase 14 — Restaurantes

Solo después del MVP médico.

## Fase 15 — Hoteles

Solo después de análisis de brecha por reservas de rango de fechas.

## Fase 12A — External Scheduling Provider Abstraction

Objetivo: diseñar la capa genérica de proveedores externos de agenda/calendario y reuniones virtuales.

Entregables:

- SchedulingProvider interface.
- MeetingProvider interface.
- InternalSchedulingProvider.
- ManualMeetingProvider.
- external_systems.
- scheduling_provider_configs.
- meeting_provider_configs.
- external mappings.
- external events.
- sync runs.
- FakeSchedulingProvider para pruebas.

## Fase 12B — Docplanner Scheduling Adapter

Objetivo: implementar Docplanner/Doctoralia como adaptador de agenda para tenants que ya lo usan como autoridad.

Entregables:

- DocplannerSchedulingProvider.
- Mapeos de doctor/facility/address/service.
- Consulta de slots.
- Consulta de bookings.
- Manejo de breaks.
- Creación de booking externo.
- Cancelación/reprogramación.
- Callbacks o pull notifications.
- Reconciliación básica.

## Fase 12C — Google Calendar Scheduling Adapter

Objetivo: implementar Google Calendar como proveedor externo de agenda.

Entregables:

- GoogleCalendarSchedulingProvider.
- Mapeo de calendarios.
- Free/busy o lectura de eventos.
- Creación de evento.
- Cancelación/reprogramación.
- Mapping de cita a evento.
- Sincronización básica.
- Posibilidad futura de Google Meet.

## Fase 12D — Microsoft Calendar and Teams Adapter

Objetivo: implementar Microsoft 365 / Outlook Calendar y Microsoft Teams mediante proveedor de agenda y proveedor de reuniones.

Entregables:

- MicrosoftCalendarSchedulingProvider.
- MicrosoftTeamsMeetingProvider.
- Microsoft Graph integration.
- Creación de eventos.
- Creación de reuniones Teams.
- Cancelación/reprogramación.
- Mapping de eventos.
- Sincronización básica.


## Fase 0B — Contratos, máquinas de estado, fixtures y checklist

Objetivo:

Cerrar la capa de precisión necesaria para que Codex implemente por fases con menos ambigüedad.

Entregables:

- `docs/API_CONTRACTS.md`
- `docs/STATE_MACHINES.md`
- `docs/SCHEDULING_PROVIDER_RULES.md`
- `docs/TEST_FIXTURES.md`
- `docs/PR_REVIEW_CHECKLIST.md`

Regla:

Esta fase no implementa código funcional de negocio. Su propósito es convertir el alcance conceptual en reglas verificables y contratos iniciales.

## Fase 0C — Estrategia de marca, verticales y repositorio

Objetivo:

Formalizar TotalChat como plataforma paraguas y MediChat como primer producto vertical.

Entregables:

- `docs/BRAND_AND_PRODUCT_STRATEGY.md`
- `docs/REPOSITORY_STRATEGY.md`
- `docs/SOLUTION_ARCHITECTURE.md`
- Actualización de constitución.
- Actualización de arquitectura.
- Actualización del modelo de datos con `solutions` y `tenant_solutions`.
- Reglas para monorepo modular.
- Reglas para separación futura de repos.

Alcance:

Esta fase no implementa nuevos verticales. Solo define nombres, límites y estructura.

Verticales oficiales:

```text
MediChat
RestoChat
HotelChat
StayChat
StoreChat
```

## Spec 015 — Campaigns and Broadcast Messaging

Objetivo:

Implementar el módulo transversal de campañas, comunicados y mensajería masiva.

Aplica a:

```text
MediChat inicialmente
RestoChat futuro
HotelChat futuro
StayChat futuro
StoreChat futuro
```

Entregables:

- `docs/CAMPAIGNS_AND_BROADCASTS.md`
- `packages/campaigns`
- `CampaignService`
- `AudienceResolver`
- `MediChatAudienceResolver`
- `CampaignDeliveryPlanner`
- `CampaignDispatcher`
- `CampaignScheduler`
- endpoints admin
- worker
- módulo admin web
- contact preferences
- delivery tracking
- métricas básicas
- auditoría

Fuera de alcance inicial:

- WhatsApp productivo;
- A/B testing;
- journeys multietapa;
- CRM avanzado;
- email marketing;
- SMS;
- adjuntos.
