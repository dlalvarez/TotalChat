# ARCHITECTURE.md  
# Arquitectura de TotalChat

## 1. Visión general

TotalChat será una plataforma SaaS conversacional multi-tenant para reservas.

El primer vertical será citas médicas y servicios profesionales de salud.

La arquitectura combina:

- Backend FastAPI.
- PostgreSQL con schema por tenant.
- pgvector para búsqueda semántica.
- Redis para estado temporal y locks.
- LangGraph para flujos conversacionales.
- OpenAI como proveedor LLM inicial.
- Consola administrativa web.
- Telegram como primer canal.
- Wompi futuro.
- n8n como automatización complementaria.

### Fase 7A.8 — tools internas de pagos

El Booking Agent accede al estado de pagos mediante un port de repositorio tenant-scoped. La implementación SQLAlchemy consulta reservas, configuración organizacional e intentos en PostgreSQL y devuelve datos estructurados. Preparar un método permitido solo crea un intento `evidence_required` para transferencia o `pending` para simulación/pago en sitio; no cambia la cita, no ocupa ni libera slots y no constituye aprobación, rechazo o evidencia.

### Fase 7A.9 — coordinador conversacional determinístico

`BookingAgent` representa la coordinación interna mínima y testeable del flujo servicio → precio → disponibilidad → cita → pago. Reutiliza las tools tenant-scoped y sus contratos estructurados, detiene el flujo ante datos ausentes o conflictos y mantiene separadas la ocupación de la cita y la preparación del pago. No incorpora todavía runtime LangGraph, LLM, red, canales, endpoints ni persistencia de conversación.

## 2. Diagrama lógico

```text
Telegram / WhatsApp
        ↓
FastAPI Webhooks
        ↓
Tenant Resolver
        ↓
Conversation State / Redis
        ↓
LangGraph Booking Agent
        ↓
Domain Tools
        ↓
Domain Services
        ↓
PostgreSQL tenant schema
        ↓
Domain Events
        ↓
n8n / Notificaciones / Recordatorios
```

Consola administrativa:

```text
Admin Web Console
        ↓
FastAPI Admin API
        ↓
Auth + Tenant Resolver
        ↓
Domain Services
        ↓
PostgreSQL tenant schema
```

## 3. Stack técnico

### Backend

- Python.
- FastAPI.
- Pydantic.
- SQLAlchemy.
- Alembic.
- Uvicorn/Gunicorn.

### IA

- LangChain.
- LangGraph.
- OpenAI inicial.
- Abstracción `LLMProvider`.

### Base de datos

- PostgreSQL.
- pgvector.
- Schema `public`.
- Schema por tenant.

### Estado temporal

- Redis.

### Frontend admin

Recomendado:

- React.
- TypeScript.
- Vite.
- Tailwind CSS.
- shadcn/ui.
- TanStack Query.
- React Hook Form.
- Zod.

### Infraestructura

- Linux.
- Docker Compose.
- Nginx.
- Let's Encrypt.
- Dominio/subdominio.

## 4. Multi-tenancy

### 4.1. Modelo elegido

TotalChat usará schema PostgreSQL por tenant.

```text
public
tenant_dra_ana
tenant_clinica_vida
tenant_dr_carlos
```

### 4.2. Schema public

Contiene control SaaS:

- tenants.
- tenant_channels.
- tenant_domains.
- tenant_settings.
- users.
- user_tenants.
- plans.
- subscriptions.
- global_audit_log.
- schema_migrations_control.

### 4.3. Schema tenant

Contiene datos operativos del tenant:

- organizations.
- locations.
- rooms.
- practitioners.
- specialties.
- practitioner_services.
- prices.
- patients.
- bookings.
- payments.
- messages.
- semantic_documents.

### 4.4. Tenant resolver

Cada petición debe resolver tenant antes de tocar datos operativos.

Fuentes posibles:

- Telegram bot token/canal.
- WhatsApp phone number ID.
- Subdominio.
- URL pública.
- Token de webhook.
- Sesión administrativa.

Flujo:

```text
Request
↓
Identify channel/domain/session
↓
Query public.tenant_channels or public.tenant_domains
↓
Get tenant.schema_name
↓
Open DB session with safe tenant context
↓
Execute domain services
```

El LLM jamás resuelve tenant.

## 5. Backend

Estructura recomendada:

```text
backend/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── api/
│   ├── auth/
│   ├── db/
│   ├── tenants/
│   ├── domain/
│   ├── booking/
│   ├── payments/
│   ├── ai/
│   ├── channels/
│   ├── events/
│   └── admin/
├── migrations/
├── tests/
└── pyproject.toml
```

## 6. Frontend administrativo

Estructura recomendada:

```text
frontend/
├── src/
│   ├── app/
│   ├── components/
│   ├── features/
│   │   ├── auth/
│   │   ├── dashboard/
│   │   ├── organizations/
│   │   ├── practitioners/
│   │   ├── services/
│   │   ├── pricing/
│   │   ├── availability/
│   │   ├── bookings/
│   │   ├── patients/
│   │   ├── payments/
│   │   └── settings/
│   ├── lib/
│   └── main.tsx
└── package.json
```

## 7. LangGraph

El agente conversacional debe usar herramientas controladas.

Flujo base:

```text
receive_message
↓
resolve_conversation_state
↓
classify_intent
↓
collect_required_context
↓
search_service_or_specialty
↓
resolve_practitioner_if_needed
↓
resolve_modality
↓
resolve_payer_plan_if_needed
↓
find_available_slots
↓
offer_slots
↓
collect_minimal_patient_data
↓
create_tentative_booking
↓
handle_payment_option
↓
confirm_or_hold_booking
↓
send_confirmation_or_pending_message
```

## 8. LLMProvider

El código de negocio, LangGraph, canales y tools no debe llamar directamente a ningún proveedor externo.

Debe existir:

```text
LLMProvider
OpenAICompatibleProvider
```

Adaptadores configurables mediante el contrato OpenAI-compatible:

```text
OpenAI
DeepInfra/Qwen
Kimi (futuro, mediante base_url/model; sin adaptador hardcodeado)
```

Variables:

```text
TOTALCHAT_LLM_PROVIDER=openai
TOTALCHAT_LLM_BASE_URL=https://api.openai.com/v1
TOTALCHAT_LLM_API_KEY=...
TOTALCHAT_LLM_MODEL=gpt-4o-mini
TOTALCHAT_LLM_TIMEOUT_SECONDS=30
TOTALCHAT_LLM_CAPTURE_REASONING=false
TOTALCHAT_EMBEDDINGS_PROVIDER=openai
TOTALCHAT_EMBEDDINGS_BASE_URL=https://api.openai.com/v1
TOTALCHAT_EMBEDDINGS_API_KEY=...
TOTALCHAT_EMBEDDINGS_MODEL=text-embedding-3-small
TOTALCHAT_EMBEDDING_DIMENSIONS=1536
```

## 9. pgvector

Cada tenant puede tener documentos semánticos propios.

Usos:

- Búsqueda de servicios.
- Especialidades.
- FAQ.
- Políticas.
- Instrucciones.
- Mensajes base.

No se usa para disponibilidad ni precio.

## 10. Redis

Usos iniciales:

- Estado de conversación.
- Holds temporales.
- Locks.
- Rate limiting.
- Cache ligera.

La verdad siempre está en PostgreSQL.

### 10.1. Contrato de estado conversacional (Fase 7A.2)

`BookingConversationState` define el contrato interno JSON para estado temporal futuro. Contiene el `tenant_id` que el backend ya resolvió y referencias internas necesarias para coordinar una reserva, pero nunca `schema_name`, razonamiento del proveedor, prompts ni secretos. La deserialización valida enums, timestamps, campos permitidos y metadata antes de aceptar el estado.

Este contrato todavía no se conecta a Redis ni a LangGraph. Tampoco consulta PostgreSQL: las referencias no constituyen confirmación de disponibilidad, precio, cita o pago, y PostgreSQL continúa como fuente de verdad.

### 10.2. Booking graph base (Fase 7A.3)

`run_booking_graph` implementa temporalmente un adapter local y determinista previo al runtime LangGraph completo. Sus nodos normalizan una copia del estado, detectan campos faltantes, clasifican y avanzan la etapa, y preparan un `BookingGraphResult` testeable.

El adapter no contiene tools reales ni acceso a DB, Redis, red o LLM. Sus acciones son señales internas de coordinación y no confirman precios, disponibilidad, citas o pagos. El backend entrega `tenant_id` ya resuelto y el graph no recibe ni selecciona `schema_name`.

### 10.3. Tools de servicios (Fase 7A.4)

`ServiceTools` opera detrás del tenant resolver con un `ServiceRepository` o una sesión SQLAlchemy ya contextualizada al schema tenant. `SQLAlchemyServiceRepository` consulta los modelos reales `practitioner_services`, `practitioners`, `organizations` y `service_modalities`, limitando resultados a recursos activos.

El contrato devuelve modelos internos estructurados con referencias, descripción, duración y modalidades. No cruza la frontera hacia precios, disponibilidad, citas o pagos; tampoco usa LLM, red, endpoints ni `schema_name`.

### 10.4. Tools de precios (Fase 7A.5)

`PricingTools` opera detrás del tenant resolver con `PricingRepository` o una sesión SQLAlchemy ya contextualizada. `SQLAlchemyPricingRepository` consulta la jerarquía comercial real `payer_type → payer → payer_plan → practitioner_service_price` y exige que el precio, el servicio, el profesional, la organización, su relación y toda la jerarquía de pagador estén activos y que el precio esté vigente para la fecha solicitada.

Las tools devuelven cotizaciones estructuradas existentes, nunca un precio genérico o calculado. No seleccionan schema, convierten moneda, consultan disponibilidad, generan slots, crean citas o pagos, ni usan LLM, red o endpoints.

### 10.5. Tools de disponibilidad (Fase 7A.6)

`AvailabilityTools` opera detrás del tenant resolver con un `AvailabilityRepository` o sesión SQLAlchemy tenant-scoped. El repository interno reutiliza los estados bloqueantes del motor de agenda y calcula slots desde reglas recurrentes, modalidades, duración, excepciones y reservas existentes en PostgreSQL.

La tool valida que servicio, profesional, organización, relación y recursos presenciales estén activos, deduplica resultados equivalentes y aplica un límite determinístico. Sus resultados no incluyen schema, precios o pagos, y consultar un slot no crea una cita ni un hold. No se agregan endpoints, LLM, red, canales ni proveedores externos.

### 10.6. Tools de citas (Fase 7A.7)

`AppointmentTools` opera con un repository o sesión tenant-scoped y vuelve a consultar `SQLAlchemyAvailabilityRepository` antes de insertar una reserva `tentative`. El bloqueo transaccional del profesional serializa creaciones concurrentes en PostgreSQL; reservas en estados bloqueantes representan ocupación real y las canceladas, expiradas o terminales no bloqueantes liberan el horario.

La tool crea los snapshots que exige el modelo de booking usando únicamente datos activos ya seleccionados. Devuelve solo identidad interna, estado y datos del slot: no expone pagos, precio o schema y no incorpora endpoints, LLM, red, canales ni proveedores externos.

## 11. Eventos de dominio

El backend debe emitir eventos.

Ejemplos:

- booking.created
- booking.confirmed
- booking.cancelled
- payment.evidence_uploaded
- payment.pending_manual_review
- payment.review_overdue
- virtual_link.pending
- reminder.due
- attendance.confirmed
- attendance.declined

n8n puede consumir eventos, pero no decide la verdad.

## 12. Despliegue

Recomendado:

```text
Linux host
├── Nginx + Certbot
└── Docker Compose
    ├── backend
    ├── frontend
    ├── postgres
    └── redis
```

Puertos externos:

- 80/443 solamente.

Puertos internos:

- backend 8000.
- postgres 5432.
- redis 6379.

## 13. Seguridad arquitectónica

Reglas:

- Resolver tenant antes de ejecutar herramientas.
- Nunca exponer schema selection al LLM.
- Auditar acciones críticas.
- Validar webhooks.
- No guardar secretos en repo.
- Hash de passwords.
- Roles por tenant.

## 14. External Scheduling and Meeting Providers

TotalChat debe soportar una capa genérica de proveedores externos de agenda y calendarios.

```text
TotalChat Booking Core
        ↓
SchedulingProvider interface
        ├── InternalSchedulingProvider
        ├── DocplannerSchedulingProvider
        ├── GoogleCalendarSchedulingProvider
        ├── MicrosoftCalendarSchedulingProvider
        └── OtherSchedulingProvider
```

También debe existir una capa separada para reuniones virtuales:

```text
MeetingProvider interface
        ├── ManualMeetingProvider
        ├── GoogleMeetProvider
        ├── MicrosoftTeamsMeetingProvider
        ├── ZoomMeetingProvider
        └── OtherMeetingProvider
```

### 14.1. SchedulingProvider

Responsable de:

- consultar disponibilidad;
- crear reservas;
- cancelar reservas;
- reprogramar reservas;
- consultar reservas externas;
- crear bloqueos;
- eliminar bloqueos;
- sincronizar eventos externos.

### 14.2. MeetingProvider

Responsable de:

- crear link de reunión;
- actualizar link de reunión;
- cancelar reunión;
- consultar link;
- guardar detalles virtuales.

### 14.3. Modos por tenant

Cada tenant, organización o profesional podrá usar:

```text
schedule_authority = totalchat | docplanner | google_calendar | microsoft_calendar | other
meeting_provider = manual | google_meet | microsoft_teams | zoom | other
```

### 14.4. Autoridad de agenda

Modos soportados:

```text
internal_authoritative
external_authoritative
hybrid
```

Si el modo es `external_authoritative`, TotalChat no debe confirmar localmente sin confirmación/reserva externa.

### 14.5. Sync mode

```text
none
read_only
write_through
bidirectional
```

El modo recomendado para evitar doble reserva con agenda externa es `write_through`, y luego `bidirectional` cuando existan callbacks o sincronización madura.

### 14.6. Implementación MVP

El MVP implementará:

```text
InternalSchedulingProvider
ManualMeetingProvider
```

Docplanner, Google Calendar, Microsoft Calendar, Google Meet y Teams serán fases futuras, pero la arquitectura debe quedar preparada.

## Arquitectura multi-solución

TotalChat debe organizarse como una plataforma multi-solución:

```text
TotalChat Platform
        ├── TotalChat Core
        ├── MediChat
        ├── RestoChat
        ├── HotelChat
        ├── StayChat
        └── StoreChat
```

El core compartido ofrece capacidades técnicas reutilizables:

- tenants;
- auth;
- conversations;
- LLM providers;
- channels;
- payments;
- scheduling providers;
- meeting providers;
- notifications;
- events;
- audit.

Los verticales contienen dominio específico.

El primer vertical funcional será:

```text
solutions/medichat/
```

La arquitectura recomendada de repo es:

```text
TotalChat/
├── apps/
│   ├── api/
│   ├── admin-web/
│   └── worker/
├── packages/
│   ├── core/
│   ├── auth/
│   ├── tenancy/
│   ├── conversations/
│   ├── ai/
│   ├── channels/
│   ├── payments/
│   ├── scheduling/
│   ├── meetings/
│   ├── notifications/
│   └── events/
└── solutions/
    ├── medichat/
    ├── restochat/
    ├── hotelchat/
    ├── staychat/
    └── storechat/
```

Regla:

```text
TotalChat Core no debe conocer detalles de MediChat.
MediChat usa capacidades del core, pero su dominio vive dentro del vertical.
```

## Campaigns and Broadcast Messaging

TotalChat Platform debe incluir un módulo transversal de campañas y comunicados.

Ubicación recomendada:

```text
packages/campaigns/
```

Flujo:

```text
Admin Console
    ↓
CampaignService
    ↓
AudienceResolver
    ↓
CampaignDeliveryPlanner
    ↓
CampaignScheduler / Worker
    ↓
ChannelProvider
    ↓
Telegram / WhatsApp / otros
    ↓
Delivery status update
    ↓
Campaign metrics
```

Integraciones:

```text
packages/campaigns
packages/channels
packages/notifications
packages/conversations
packages/events
solutions/medichat audience resolver
```

Regla:

```text
Campañas es plataforma/core. Los resolvers de audiencia pueden ser específicos por vertical.
```


## 7A.1. Providers IA y documentos semánticos

La Fase 7A.1.1 agrega `OpenAICompatibleProvider` como adaptador común para OpenAI y DeepInfra/Qwen. La selección ocurre mediante configuración genérica, nunca por imports desde lógica futura de LangGraph. `TOTALCHAT_LLM_API_KEY` es la única variable de credencial LLM para OpenAI, DeepInfra/Qwen, Kimi futuro y cualquier proveedor OpenAI-compatible; no existe fallback a variables específicas de proveedor. Embeddings defaulta provider, base URL y credencial a la configuración LLM. Kimi puede configurarse en el futuro por `base_url` y `model`, sin acoplamiento ni fallback automático.

No existe un adaptador separado para OpenAI. OpenAI, DeepInfra/Qwen y Kimi futuro son configuraciones de `OpenAICompatibleProvider`, no clases concretas distintas. Todo consumidor futuro debe depender de `LLMProvider`/`EmbeddingsProvider` y obtener instancias mediante `create_llm_provider()` o `create_embeddings_provider()`.

LLM y embeddings pueden usar proveedores distintos. El ejemplo operativo usa DeepInfra/Qwen para LLM y OpenAI `text-embedding-3-small` para embeddings de 1536 dimensiones. Si las variables específicas de embeddings se omiten, heredan provider, URL y credencial del LLM; quien use ese default debe configurar un modelo de embeddings válido para el proveedor efectivo. Cambiar a DeepInfra/Qwen Embedding exige verificar y documentar la dimensión real del modelo antes de guardar vectores o cambiar `TOTALCHAT_EMBEDDING_DIMENSIONS`, porque `semantic_documents.embedding VECTOR(...)` depende de ella y una variación de dimensión requiere tratamiento explícito de los datos existentes.

El adaptador normaliza únicamente `choices[0].message.content` como respuesta visible. `reasoning_content` es metadata técnica opcional: no se mezcla con `content`, no se muestra a usuarios, frontend o canales, y no se guarda ni registra por defecto. Solo puede incluirse en `LLMResponse.metadata` con `TOTALCHAT_LLM_CAPTURE_REASONING=true` para diagnóstico técnico y tuning de prompts; esta fase no implementa su persistencia ni evaluación formal. Ninguna lógica de negocio, tool, pago, cita, disponibilidad, autorización o resolución de tenant puede depender de esa metadata. Las claves nunca se registran; toda clave expuesta en conversaciones debe rotarse.

Los documentos semánticos se almacenan en `semantic_documents` dentro de cada schema tenant. No viven en `public`, no incluyen `schema_name` y toda operación futura de IA debe recibir el tenant ya resuelto por backend antes de consultar embeddings o tools. Esta fase no agrega LangGraph, tools de dominio, endpoints HTTP, canales ni RAG completo.

## Entrada Telegram — Fase 8A.1

`POST /api/webhooks/telegram/{webhook_secret}` valida un secreto configurado por
entorno y resuelve el tenant mediante el identificador del bot contra
`public.tenant_channels`. Solo después de esa resolución el backend selecciona
internamente el schema tenant, crea o reutiliza `conversation_sessions` y guarda
el mensaje en `messages`. El `update_id` de Telegram evita duplicar mensajes.

Esta entrada no llama al Booking Agent, al LLM, a la red ni a un cliente Telegram;
tampoco envía respuestas salientes. El payload, las respuestas HTTP y la metadata
persistida no contienen secretos ni `schema_name`.

## Puente interno Telegram — Fase 8A.2

El `TelegramWebhookService` conserva la frontera HTTP ligera: resuelve tenant,
persiste el mensaje entrante y delega a un `BookingAgentInvoker`. El adaptador
determinístico crea el agente 7A.9 con tools SQLAlchemy ya contextualizadas y una
request interna de campos permitidos. La salida se registra en `messages` como
`direction=outgoing` y `delivery_status=pending`; no existe todavía cliente
Telegram saliente, llamada de red, LLM, LangGraph runtime ni transición a enviado.

## Entrega Telegram — Fase 8A.3

Tras hacer durable el `outgoing pending`, el adaptador Telegram usa la credencial
de entorno para entregar exactamente ese texto. La confirmación de la Bot API se
persiste como `sent`; los errores sanitizados se persisten como `failed` sin
reprocesar el agente ni romper el acuse del webhook. La idempotencia del update
impide un segundo envío. No se agregan reintentos, jobs, colas, LLM o LangGraph.
