# TotalChat

TotalChat es una plataforma conversacional multi-tenant para reservas, iniciando con el vertical de citas médicas y servicios profesionales de salud.

El sistema combina:

- Backend propio con FastAPI.
- PostgreSQL como fuente de verdad.
- Multi-tenancy mediante schema PostgreSQL por tenant.
- pgvector para búsqueda semántica.
- Redis para estado temporal, holds y locks.
- LangGraph/LangChain para el agente conversacional.
- OpenAI como proveedor LLM inicial.
- Abstracción LLMProvider para permitir proveedores futuros como Ollama.
- Consola administrativa web.
- Telegram como primer canal.
- WhatsApp como canal futuro.
- Pagos simulados inicialmente.
- Wompi como pasarela futura.
- Transferencias con evidencia y revisión manual.
- Recordatorios y confirmación de asistencia.
- n8n como automatización complementaria, no como core.

## Documentos principales

- `docs/CONSTITUTION.md`: reglas rectoras obligatorias.
- `docs/ARCHITECTURE.md`: arquitectura técnica y decisiones estructurales.
- `docs/DATA_MODEL.md`: modelo de datos conceptual.
- `docs/ROADMAP.md`: roadmap por fases.
- `docs/AI_BOUNDARIES.md`: límites y responsabilidades de IA.
- `docs/PAYMENTS.md`: reglas de pagos, transferencias, Wompi y revisión manual.
- `docs/ADMIN_CONSOLE.md`: alcance de la consola administrativa.
- `docs/SECURITY.md`: seguridad, privacidad, auditoría y multi-tenancy.
- `docs/DECISIONS.md`: decisiones cerradas y abiertas.
- `docs/SDD_SPECKIT_GUIDE.md`: guía para SDD y Spec Kit.
- `docs/MVP_001_SPEC.md`: especificación funcional del MVP inicial.
- `docs/INTEGRATIONS_EXTERNAL_CALENDARS.md`: arquitectura de proveedores externos de agenda, calendarios y reuniones virtuales.

## Specs iniciales

- `specs/001-project-foundation/`
- `specs/002-multitenancy/`
- `specs/003-booking-domain/`
- `specs/004-admin-console/`
- `specs/005-langgraph-agent/`
- `specs/006-telegram-channel/`
- `specs/007-payments-manual-review/`
- `specs/008-reminders-confirmation/`
- `specs/011-external-scheduling-provider/`
- `specs/012-docplanner-adapter/`
- `specs/013-google-calendar-adapter/`
- `specs/014-microsoft-calendar-teams-adapter/`

## Regla principal

TotalChat no debe iniciar como un bot aislado. Debe iniciar como una plataforma de reservas multi-tenant con backend, modelo de datos, consola administrativa y agente conversacional.


## Documentos de precisión para implementación con Codex

La versión 3 agrega documentos para que Codex tenga contratos y reglas ejecutables por fase:

- `docs/API_CONTRACTS.md`: contratos REST iniciales y convenciones de API.
- `docs/STATE_MACHINES.md`: máquinas de estado de citas, pagos, evidencia, asistencia, reembolsos y agenda externa.
- `docs/SCHEDULING_PROVIDER_RULES.md`: reglas de SchedulingProvider y MeetingProvider.
- `docs/TEST_FIXTURES.md`: datos demo y escenarios de prueba obligatorios.
- `docs/PR_REVIEW_CHECKLIST.md`: checklist para revisar cada PR generado por Codex.

## Estrategia de marca y verticales

TotalChat es la marca paraguas y plataforma técnica multi-solución.

Verticales oficiales definidos:

- **MediChat**: médicos y profesionales de salud.
- **RestoChat**: restaurantes y bares.
- **HotelChat**: hoteles.
- **StayChat**: Airbnb y otros alojamientos.
- **StoreChat**: tiendas, compras y comercio minorista.

El primer vertical a implementar es **MediChat**.

La estructura técnica debe separar:

- `apps/`: aplicaciones ejecutables.
- `packages/`: capacidades compartidas de plataforma.
- `solutions/`: verticales de negocio.
- `solutions/medichat/`: primer vertical funcional.

## Campañas y comunicados

TotalChat debe incluir un módulo transversal de campañas, comunicados y mensajería masiva para todos los verticales.

Primera aplicación: **MediChat**.

Casos de uso:

- avisos operativos;
- cierres por vacaciones;
- cambios de horario;
- promociones;
- apertura de agenda;
- recordatorios masivos;
- campañas segmentadas.

Documento principal:

- `docs/CAMPAIGNS_AND_BROADCASTS.md`

Spec:

- `specs/015-campaigns-broadcast-messaging/`
