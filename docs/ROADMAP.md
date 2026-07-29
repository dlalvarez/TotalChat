# ROADMAP.md  
# Roadmap de TotalChat

## Fase 0 — Gobierno documental y SDD

Estado: implementada.

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

## Fase 0B — Estrategia de marca, repositorio y verticales

Estado: implementada.

Objetivo: documentar TotalChat como plataforma paraguas, MediChat como primer vertical MVP, verticales futuras y monorepo modular.

Entregables:

- BRAND_AND_PRODUCT_STRATEGY.md.
- REPOSITORY_STRATEGY.md.
- Decisiones de verticales oficiales.
- Reglas de monorepo modular.
- RestoChat, HotelChat, StayChat y StoreChat documentados como futuros, nunca antes del MVP MediChat.

## Fase 0C — Precisión ejecutable para Codex

Estado: implementada.

Objetivo: agregar contratos, máquinas de estado, fixtures y checklist para reducir ambigüedad durante implementación.

Entregables:

- API_CONTRACTS.md.
- STATE_MACHINES.md.
- SCHEDULING_PROVIDER_RULES.md.
- TEST_FIXTURES.md.
- PR_REVIEW_CHECKLIST.md.

## Fase 0D — Alineación documental post-backend Fase 5

Estado: implementada por esta alineación documental.

Objetivo: alinear documentación rectora después de la implementación backend de foundation, multitenancy, booking domain, endpoints admin de citas y pagos manuales/simulados.

Entregables:

- Numeración coherente en CONSTITUTION.md.
- Roadmap ordenado cronológicamente.
- Contratos API de pagos alineados con la API manual/simulada implementada.
- Modelo de datos, políticas y máquinas de estado de pagos alineadas con Spec 007.
- Wompi, WhatsApp, campañas, agenda externa y verticales no médicas preservadas como futuro.

## Fase 1 — Fundación técnica

Estado: backend implementado y validado.

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

Estado: backend implementado y validado con PostgreSQL schema-per-tenant.

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

Estado: backend implementado y validado.

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

Estado: backend baseline implementado; creación de booking admin y snapshots validados en integración ligera. Validación completa de disponibilidad, generación de slots, confirmación, cancelación y reprogramación pendiente de pruebas específicas.

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

Estado: backend implementado y validado con PostgreSQL schema-per-tenant. PR #26 corrigió el orden de transacciones tenant-scoped alrededor de `SET LOCAL search_path`.

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
- Revisión vencida sin liberar slot por defecto.

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
- OpenAICompatibleProvider.
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

### Secuencia interna de realineación y runtime conversacional

- **Fase 8A.6 — Realineación SDD del ciclo conversacional grounded.** Estado:
  documental y contractual. Define la responsabilidad conversacional del LLM,
  la autoridad operacional del backend, las tools como frontera única y
  PostgreSQL como fuente de verdad. No implementa runtime ni código funcional.
- **Fase 8A.7 — Runtime conversacional natural básico.** Estado: implementada.
  Es agnóstico de canal, depende de `LLMProvider`, usa contexto reciente seguro y
  fallback técnico controlado, y no incorpora tools operativas.
- **Fase 8A.8 — Tool calling de servicios.** Estado: implementada. Incorpora
  exclusivamente `search_services`, tenant-scoped y de solo lectura, con
  argumentos cerrados y resultado visible sin UUID ni datos de infraestructura.
- **Fase 8A.9 — Contexto inicial de reserva.** Estado: implementada. Incorpora
  intención, etapa, contexto recolectado e información faltante persistentes,
  sin adelantar disponibilidad, reservas, pagos o LangGraph.

La respuesta fija de 8A.5 fue una implementación transitoria que validó estado
incompleto, persistencia y entrega; no representa la redacción definitiva. Se
conservan su idempotencia y fronteras de canal. 8A.7 sustituyó la conversación
normal por generación LLM sin incorporar operaciones.

Precios, disponibilidad, selección de slots, creación de reservas y pagos se
incorporarán incrementalmente después de validar servicios y contexto
conversacional. No se numeran ni cierran todavía: su detalle exige revisar este
roadmap y autorización posterior. El contrato rector de esta secuencia está en
[`CONVERSATION_ORCHESTRATION.md`](CONVERSATION_ORCHESTRATION.md).

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

Objetivo: pasarela real futura en pruebas, solo después de pagos simulados/manuales.

Entregables:

- Crear link.
- Webhook.
- Validación.
- Confirmar pago.
- Confirmar cita.

## Fase 12 — WhatsApp

Objetivo: canal comercial futuro, solo después de Telegram.

Entregables:

- Webhook WhatsApp.
- Resolver tenant por número.
- Enviar/recibir mensajes.
- Plantillas si aplica.

## Fase 13 — n8n complementario

Objetivo: automatizaciones externas complementarias, no core.

Entregables:

- Domain events.
- Webhooks salientes.
- Recordatorios.
- Alertas.
- Encuestas.

## Fase 14 — External Scheduling Provider Abstraction

Objetivo: diseñar la capa genérica futura de proveedores externos de agenda/calendario y reuniones virtuales.

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

## Fase 15 — Docplanner Scheduling Adapter

Objetivo: implementar Docplanner/Doctoralia como adaptador futuro de agenda para tenants que ya lo usan como autoridad.

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

## Fase 16 — Google Calendar Scheduling Adapter

Objetivo: implementar Google Calendar como proveedor externo futuro de agenda.

Entregables:

- GoogleCalendarSchedulingProvider.
- Mapeo de calendarios.
- Free/busy o lectura de eventos.
- Creación de evento.
- Cancelación/reprogramación.
- Mapping de cita a evento.
- Sincronización básica.
- Posibilidad futura de Google Meet.

## Fase 17 — Microsoft Calendar and Teams Adapter

Objetivo: implementar Microsoft Calendar como proveedor externo futuro de agenda y Teams como proveedor futuro de reuniones virtuales.

## Fase 18 — Campañas, comunicados y mensajería masiva

Objetivo: implementar la capacidad transversal futura definida en Spec 015, con TotalChat como fuente de verdad y n8n solo complementario.

Entregables:

- Campañas desde consola admin.
- Segmentación por audiencia.
- Consentimiento y preferencias.
- Entregas individuales auditadas.
- ChannelProvider.

## Fase 19 — RestoChat

Solo después del MVP MediChat.

## Fase 20 — HotelChat

Solo después del MVP MediChat y análisis de brecha por reservas de rango de fechas.
