# TotalChat - Documentación Completa Consolidada v5

Documento consolidado para SDD, Spec Kit y Codex.

Esta versión incorpora el módulo transversal de campañas, comunicados y mensajería masiva.

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



---

# BRAND_AND_PRODUCT_STRATEGY.md
# Estrategia de marca, plataforma y verticales de TotalChat

## 1. Propósito

Este documento define cómo debe manejarse la relación entre **TotalChat** y las soluciones verticales construidas sobre la plataforma.

La decisión principal es que **TotalChat no será tratado únicamente como una app o producto vertical**, sino como una **marca paraguas, plataforma técnica y familia de soluciones conversacionales**.

El primer producto vertical será **MediChat**, enfocado en citas médicas y profesionales de salud.

## 2. Decisión principal

TotalChat será la plataforma paraguas.

Las soluciones verticales oficiales iniciales serán:

```text
TotalChat
├── MediChat   → médicos y profesionales de salud
├── RestoChat  → restaurantes y bares
├── HotelChat  → hoteles
├── StayChat   → Airbnb y otros alojamientos
└── StoreChat  → tiendas, compras y comercio minorista
```

## 3. Definición de TotalChat

TotalChat representa:

- La marca paraguas.
- La plataforma técnica común.
- El framework SaaS multi-tenant.
- La base de conversación, canales, pagos, agenda, usuarios, providers, seguridad y automatizaciones.
- La familia de productos verticales.

TotalChat no debe entenderse como “la app médica”. La app médica es MediChat.

## 4. Definición de TotalChat Platform

**TotalChat Platform** es el conjunto de componentes técnicos compartidos que permiten construir verticales conversacionales.

Incluye:

- Multi-tenancy.
- Auth.
- Usuarios y roles.
- Tenant resolver.
- Canales conversacionales.
- Conversaciones y mensajes.
- LLMProvider.
- EmbeddingsProvider.
- PaymentProvider.
- SchedulingProvider.
- MeetingProvider.
- NotificationProvider.
- Eventos de dominio.
- Auditoría.
- Seguridad.
- Admin shell.
- Configuración base.
- Integraciones externas.
- Infraestructura.
- SDD/spec framework.

## 5. Definición de TotalChat Core

**TotalChat Core** representa capacidades comunes y reutilizables que no pertenecen a un vertical específico.

No debe contener reglas médicas, reglas de restaurantes, reglas hoteleras ni reglas de retail.

Ejemplos permitidos en core:

```text
tenant management
auth
roles
conversation sessions
messages
channel abstraction
LLM provider abstraction
payment provider abstraction
scheduling provider abstraction
meeting provider abstraction
audit
events
settings
logging
errors
security helpers
```

Ejemplos que NO deben ir en core:

```text
patients
medical specialties
practitioners as medical doctors
payer plans specific to healthcare
restaurant tables
hotel rooms as inventory
retail carts
```

Esos conceptos deben vivir en sus soluciones verticales.

## 6. Verticales oficiales

## 6.1. MediChat

Vertical para médicos y profesionales de salud.

### Propósito

Permitir a pacientes reservar citas médicas, psicológicas, odontológicas, terapéuticas o de otros profesionales de salud mediante conversación.

### Dominio específico

MediChat puede incluir:

- Pacientes.
- Profesionales de salud.
- Especialidades.
- Servicios del profesional.
- Modalidades de atención.
- Citas presenciales.
- Citas virtuales.
- Pagadores.
- Planes.
- Pólizas.
- Medicina prepagada.
- EPS.
- Tarifas por plan.
- Transferencias con revisión manual.
- Confirmación de asistencia.
- Integración Docplanner como proveedor externo.
- Restricción explícita de no diagnóstico médico.

### Regla

MediChat no debe contaminar TotalChat Core con conceptos médicos.

## 6.2. RestoChat

Vertical para restaurantes y bares.

### Propósito

Permitir reservas conversacionales en restaurantes, bares, cafés, gastrobares u otros negocios de comida y bebida.

### Dominio futuro posible

RestoChat puede incluir:

- Mesas.
- Zonas.
- Salones.
- Número de personas.
- Turnos.
- Tiempo máximo de ocupación.
- Lista de espera.
- Preferencias.
- Ocasiones especiales.
- Reservas para eventos.
- Depósitos.
- Políticas de cancelación.
- Confirmación de asistencia.
- Menú.
- Pedidos futuros.
- Integraciones POS futuras.

### Regla

RestoChat no debe reutilizar conceptos médicos como pacientes, EPS, pólizas o especialidades médicas.

## 6.3. HotelChat

Vertical para hoteles.

### Propósito

Permitir reservas conversacionales para hoteles tradicionales.

### Dominio futuro posible

HotelChat puede incluir:

- Habitaciones.
- Tipos de habitación.
- Tarifas por noche.
- Ocupación.
- Check-in.
- Check-out.
- Temporadas.
- Disponibilidad por rango de fechas.
- Políticas de cancelación.
- Pagos parciales.
- Confirmaciones.
- Integraciones PMS.
- Channel managers.

### Regla

HotelChat maneja inventario por noche/rango de fechas, por lo que no debe asumirse que usa el mismo modelo de slots horarios de MediChat.

## 6.4. StayChat

Vertical para Airbnb y otros alojamientos.

### Propósito

Permitir reservas conversacionales para alojamientos no necesariamente hoteleros.

### Dominio futuro posible

StayChat puede incluir:

- Apartamentos.
- Casas.
- Fincas.
- Cabañas.
- Hostales.
- Glamping.
- Estadías por noche.
- Limpieza.
- Depósitos.
- Reglas de casa.
- Check-in autónomo.
- Huéspedes.
- Integraciones con plataformas externas.

### Regla

StayChat puede compartir conceptos con HotelChat, pero no debe forzarse a ser igual. Airbnb y alojamientos particulares suelen tener reglas distintas a hoteles.

## 6.5. StoreChat

Vertical para tiendas, compras y comercio minorista.

### Propósito

Permitir atención conversacional para tiendas y comercio minorista.

### Dominio futuro posible

StoreChat puede incluir:

- Catálogo de productos.
- Categorías.
- Inventario.
- Carrito.
- Pedidos.
- Entregas.
- Recogida en tienda.
- Pagos.
- Promociones.
- Clientes.
- Conversación de venta.
- Integraciones e-commerce.
- Integraciones POS.

### Regla

StoreChat no debe mezclarse con reservas médicas ni agenda por defecto. Puede usar pagos, canales, conversación y notificaciones del core, pero su dominio principal es venta/pedido/inventario.

## 7. Naming oficial

## 7.1. Marca paraguas

```text
TotalChat
```

## 7.2. Plataforma técnica

```text
TotalChat Platform
```

## 7.3. Core compartido

```text
TotalChat Core
```

## 7.4. Soluciones verticales

```text
MediChat
RestoChat
HotelChat
StayChat
StoreChat
```

## 7.5. Códigos internos de solución

Para carpetas, slugs, paquetes, specs y configuración, usar minúsculas:

```text
medichat
restochat
hotelchat
staychat
storechat
```

## 8. Reglas de comunicación comercial

### 8.1. Cuando se hable de la familia

Usar:

```text
TotalChat
```

Ejemplo:

> TotalChat es una plataforma conversacional multi-solución para reservas, atención y comercio.

### 8.2. Cuando se hable de salud

Usar:

```text
MediChat
```

Ejemplo:

> MediChat permite a médicos y profesionales de salud gestionar citas conversacionales con pagos, recordatorios y agenda.

### 8.3. Cuando se hable de restaurantes

Usar:

```text
RestoChat
```

Ejemplo:

> RestoChat permite a restaurantes y bares gestionar reservas, confirmaciones y lista de espera por canales conversacionales.

### 8.4. Cuando se hable de hoteles

Usar:

```text
HotelChat
```

### 8.5. Cuando se hable de Airbnb/alojamientos

Usar:

```text
StayChat
```

### 8.6. Cuando se hable de tiendas

Usar:

```text
StoreChat
```

## 9. Reglas para documentación

Los documentos generales deben decir:

```text
TotalChat Platform
```

cuando hablen de capacidades comunes.

Los documentos del vertical médico deben decir:

```text
MediChat
```

cuando hablen de pacientes, profesionales de salud, especialidades, pólizas, prepagada, EPS, citas médicas o Docplanner.

## 10. Regla anti-contaminación de dominio

El dominio de MediChat no debe invadir TotalChat Core.

Ejemplos incorrectos:

```text
packages/core/patients.py
packages/core/medical_specialties.py
packages/core/eps.py
```

Ejemplos correctos:

```text
solutions/medichat/domain/patients.py
solutions/medichat/domain/specialties.py
solutions/medichat/domain/payers.py
```

## 11. Regla para Codex

Codex debe respetar esta separación:

```text
core = reusable platform capabilities
solutions/medichat = healthcare domain
solutions/restochat = restaurant domain
solutions/hotelchat = hotel domain
solutions/staychat = accommodation domain
solutions/storechat = retail domain
```

Codex no debe implementar lógica médica en paquetes compartidos salvo abstracciones genéricas.



---

# REPOSITORY_STRATEGY.md
# Estrategia de repositorios, monorepo y separación futura

## 1. Propósito

Este documento define cómo se organizarán los repositorios y la estructura interna del proyecto TotalChat.

La decisión principal es iniciar con un **monorepo modular**, preparado para una separación futura por core y verticales cuando el producto madure.

## 2. Decisión principal

TotalChat iniciará como un monorepo.

Repositorio recomendado:

```text
TotalChat
```

o, si se prefiere naming más técnico:

```text
totalchat-platform
```

Dado que ya se definió el repositorio como `TotalChat`, se mantiene:

```text
TotalChat
```

## 3. Razón para monorepo inicial

El monorepo inicial es preferible porque:

- El usuario inicia como desarrollador principal.
- El core aún no está estabilizado.
- MediChat será el primer vertical.
- Los patrones de providers, auth, tenancy, pagos, agenda y admin aún deben madurar.
- Separar repos demasiado pronto aumenta complejidad.
- SDD y Codex pueden operar mejor con contexto integral.
- Es más fácil refactorizar fronteras al inicio.

## 4. Riesgo de monorepo

Riesgos:

- Que todo termine mezclado.
- Que MediChat contamine el core.
- Que futuros verticales queden acoplados al dominio médico.
- Que el repo crezca sin límites claros.

Mitigación:

- Carpetas separadas.
- Reglas de importación.
- Documentación de límites.
- Checklist de PR.
- Specs por vertical.
- Packages compartidos solo para capacidades reutilizables.
- No promover código a core sin justificar reutilización.

## 5. Estructura recomendada

```text
TotalChat/
├── README.md
├── .env.example
├── docs/
├── specs/
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
│   ├── events/
│   └── shared/
├── solutions/
│   ├── medichat/
│   ├── restochat/
│   ├── hotelchat/
│   ├── staychat/
│   └── storechat/
├── infra/
├── scripts/
└── tests/
```

## 6. apps/

Contiene aplicaciones ejecutables.

### 6.1. apps/api

Backend principal FastAPI.

Responsabilidades:

- API REST.
- Webhooks.
- Admin API.
- Agent endpoints.
- Integración con packages y solutions.

### 6.2. apps/admin-web

Consola administrativa web.

Responsabilidades:

- Login.
- Dashboard.
- CRUDs.
- Pagos.
- Agenda.
- Configuración.
- Pantallas específicas por vertical.

### 6.3. apps/worker

Procesos en background.

Responsabilidades:

- Recordatorios.
- Expiración de reservas.
- Revisión vencida.
- Sincronizaciones.
- Eventos.
- Jobs de embeddings.
- Workers futuros.

## 7. packages/

Contiene capacidades compartidas de plataforma.

### 7.1. packages/core

Contiene utilidades y abstracciones base.

Permitido:

- config;
- logging;
- errors;
- result types;
- audit primitives;
- base domain events;
- common validators;
- time utilities;
- feature flags.

Prohibido:

- patients;
- doctors;
- medical specialties;
- restaurant tables;
- hotel inventory;
- shopping cart domain.

### 7.2. packages/auth

Contiene autenticación y autorización.

- users;
- roles;
- JWT;
- password hashing;
- permissions;
- session handling.

### 7.3. packages/tenancy

Contiene multi-tenancy.

- tenants;
- tenant_channels;
- tenant_domains;
- tenant_solutions;
- tenant resolver;
- schema provisioning;
- tenant context;
- migrations control.

### 7.4. packages/conversations

Contiene conversación común.

- conversation_sessions;
- messages;
- message state;
- channel-neutral message model;
- conversation history.

### 7.5. packages/ai

Contiene abstracciones de IA.

- LLMProvider;
- OpenAIProvider;
- EmbeddingsProvider;
- prompt registry;
- tool execution framework;
- guardrails;
- AI audit.

No debe contener prompts médicos específicos; esos van en `solutions/medichat/agent`.

### 7.6. packages/channels

Contiene canales.

- ChannelProvider;
- TelegramProvider;
- WhatsAppProvider futuro;
- WebChatProvider futuro.

### 7.7. packages/payments

Contiene pagos comunes.

- PaymentProvider;
- SimulatedPaymentProvider;
- ManualTransferProvider;
- WompiProvider futuro;
- payment attempts;
- evidence;
- manual review;
- refunds.

Debe ser suficientemente genérico para MediChat, RestoChat, HotelChat, StayChat y StoreChat.

### 7.8. packages/scheduling

Contiene agenda/calendario común.

- SchedulingProvider;
- InternalSchedulingProvider;
- external mappings;
- provider registry;
- availability abstractions.

No debe contener reglas médicas específicas.

### 7.9. packages/meetings

Contiene reuniones virtuales.

- MeetingProvider;
- ManualMeetingProvider;
- GoogleMeetProvider futuro;
- MicrosoftTeamsMeetingProvider futuro;
- ZoomMeetingProvider futuro.

### 7.10. packages/notifications

Contiene notificaciones comunes.

- NotificationProvider;
- message templates comunes;
- reminder dispatch;
- event notifications.

### 7.11. packages/events

Contiene eventos comunes.

- domain event bus;
- outbox;
- n8n dispatch futuro;
- event processing.

### 7.12. packages/shared

Contiene tipos y utilidades compartidas entre apps.

## 8. solutions/

Contiene verticales de negocio.

## 8.1. solutions/medichat

Primer vertical.

Estructura recomendada:

```text
solutions/medichat/
├── README.md
├── docs/
├── specs/
├── domain/
│   ├── patients/
│   ├── practitioners/
│   ├── specialties/
│   ├── services/
│   ├── pricing/
│   ├── appointments/
│   └── clinical_boundaries/
├── api/
├── admin/
├── agent/
├── migrations/
├── fixtures/
└── tests/
```

Responsabilidades:

- pacientes;
- profesionales de salud;
- especialidades;
- servicios médicos/profesionales;
- planes/pólizas/prepagada/EPS;
- tarifas por plan;
- citas;
- reglas de no diagnóstico;
- prompts específicos de salud;
- flujos conversacionales médicos;
- integración Docplanner específica.

## 8.2. solutions/restochat

Vertical futuro.

Responsabilidades futuras:

- mesas;
- zonas;
- reservas por número de personas;
- turnos;
- lista de espera;
- depósitos;
- eventos;
- políticas de cancelación.

## 8.3. solutions/hotelchat

Vertical futuro.

Responsabilidades futuras:

- habitaciones;
- tipos de habitación;
- tarifas por noche;
- check-in/check-out;
- disponibilidad por rango;
- PMS/channel manager.

## 8.4. solutions/staychat

Vertical futuro.

Responsabilidades futuras:

- alojamientos tipo Airbnb;
- reglas de casa;
- limpieza;
- depósitos;
- estadías;
- check-in autónomo.

## 8.5. solutions/storechat

Vertical futuro.

Responsabilidades futuras:

- productos;
- catálogo;
- inventario;
- carrito;
- pedidos;
- entregas;
- pagos;
- promociones.

## 9. specs/

Las specs pueden organizarse de dos formas.

### 9.1. Specs globales

Para plataforma:

```text
specs/000-implementation-precision/
specs/001-project-foundation/
specs/002-multitenancy/
specs/011-external-scheduling-provider/
```

### 9.2. Specs por vertical

Para MediChat:

```text
specs/003-medichat-booking-domain/
specs/005-medichat-booking-agent/
```

O dentro del vertical:

```text
solutions/medichat/specs/
```

## 10. Decisión inicial sobre ubicación de specs

Para la etapa inicial, mantener specs en la raíz:

```text
specs/
```

pero nombrar claramente las que pertenecen a MediChat.

Ejemplo:

```text
003-medichat-booking-domain
005-medichat-booking-agent
```

Si más adelante hay muchos verticales, mover specs específicas a cada `solutions/<vertical>/specs`.

## 11. Políticas de importación

### 11.1. Core no importa soluciones

Prohibido:

```text
packages/core -> solutions/medichat
packages/scheduling -> solutions/medichat
packages/payments -> solutions/medichat
```

### 11.2. Soluciones sí pueden importar packages

Permitido:

```text
solutions/medichat -> packages/core
solutions/medichat -> packages/scheduling
solutions/medichat -> packages/payments
```

### 11.3. Soluciones no deben importarse entre sí

Prohibido:

```text
solutions/restochat -> solutions/medichat
solutions/storechat -> solutions/hotelchat
```

Si algo es común, debe promoverse a `packages/` después de justificar reutilización.

### 11.4. Apps pueden orquestar packages y solutions

Permitido:

```text
apps/api -> packages/*
apps/api -> solutions/medichat
apps/admin-web -> packages/shared
apps/admin-web -> solutions/medichat admin modules
```

## 12. Cuándo separar repos

No separar repos al inicio.

Separar cuando se cumplan varias condiciones:

- MediChat tiene clientes reales.
- RestoChat u otro vertical entra en implementación real.
- Core está estable.
- Hay equipos diferentes por vertical.
- Releases se vuelven independientes.
- El monorepo empieza a generar fricción.
- Se necesita comercializar o desplegar verticales de forma separada.

## 13. Posible separación futura

Repos futuros posibles:

```text
totalchat-core
totalchat-platform-api
totalchat-admin-web
medichat
restochat
hotelchat
staychat
storechat
totalchat-infra
totalchat-docs
```

## 14. Política de versionamiento futuro

Cuando se separen repos:

- `totalchat-core` tendrá versionamiento propio.
- Cada vertical declarará versión mínima compatible del core.
- La API platform mantendrá compatibilidad con verticales.
- Se usarán releases semánticos.
- Se mantendrán changelogs por repo.

## 15. Regla para Codex

Codex debe respetar:

```text
Core reusable first, vertical domain isolated.
```

No debe crear código médico en packages compartidos.

No debe crear código de restaurantes dentro de MediChat.

No debe mover lógica a core solo porque sea cómodo.

Promover a core requiere justificación explícita:

```text
Esta funcionalidad es reusable por al menos dos verticales o es una abstracción técnica común.
```

## 16. packages/campaigns

TotalChat debe incluir un paquete transversal:

```text
packages/campaigns/
```

Responsabilidades:

- campañas;
- comunicados;
- audiencias;
- preferencias de contacto;
- entregas;
- métricas;
- programación;
- auditoría.

Este paquete puede depender de:

```text
packages/channels
packages/notifications
packages/events
packages/tenancy
```

No debe depender directamente de `solutions/medichat`.

Los resolvers específicos de vertical sí pueden vivir en cada solución:

```text
solutions/medichat/campaigns/audience_resolver.py
solutions/restochat/campaigns/audience_resolver.py futuro
```



---

# SOLUTION_ARCHITECTURE.md
# Arquitectura multi-solución de TotalChat

## 1. Propósito

Este documento define cómo TotalChat debe soportar múltiples soluciones verticales sin mezclar dominios.

## 2. Modelo conceptual

```text
TotalChat Platform
        │
        ├── TotalChat Core
        │
        ├── MediChat
        ├── RestoChat
        ├── HotelChat
        ├── StayChat
        └── StoreChat
```

## 3. Capas

### 3.1. Platform Layer

Responsable de SaaS y operación común.

Incluye:

- tenants;
- users;
- roles;
- subscriptions;
- auth;
- tenant_solutions;
- billing futuro;
- audit global;
- configuration.

### 3.2. Core Capability Layer

Responsable de capacidades reutilizables.

Incluye:

- conversations;
- AI providers;
- channel providers;
- payment providers;
- scheduling providers;
- meeting providers;
- notifications;
- events;
- audit primitives.

### 3.3. Solution Layer

Responsable de dominio específico.

Incluye:

- MediChat domain.
- RestoChat domain.
- HotelChat domain.
- StayChat domain.
- StoreChat domain.

### 3.4. Application Layer

Responsable de exponer interfaces ejecutables.

Incluye:

- API.
- Admin web.
- Worker.
- Webhooks.
- Future public booking UI.

## 4. Soluciones en public schema

Agregar entidad conceptual:

```text
solutions
├── id
├── code
├── name
├── description
├── status
├── created_at
├── updated_at
```

Códigos:

```text
medichat
restochat
hotelchat
staychat
storechat
```

Entidad:

```text
tenant_solutions
├── id
├── tenant_id
├── solution_id
├── status
├── settings
├── created_at
├── updated_at
```

Esto permite que un tenant tenga una o varias soluciones.

Ejemplo simple:

```text
Tenant Consultorio Ana → MediChat
```

Ejemplo futuro:

```text
Tenant Club Campestre
├── RestoChat
├── HotelChat
└── EventChat futuro
```

Aunque solo MediChat se implemente inicialmente, el modelo debe reconocer que TotalChat es multi-solución.

## 5. Tenant y solución

Un tenant puede tener:

```text
one_solution
multiple_solutions_future
```

Para MVP:

```text
tenant_solutions = medichat
```

## 6. Configuración por solución

Cada solución puede tener settings propios.

Ejemplo MediChat:

```json
{
  "allow_manual_transfer": true,
  "require_payment_before_confirmation": true,
  "default_schedule_authority": "internal"
}
```

Ejemplo RestoChat futuro:

```json
{
  "default_party_size": 2,
  "table_hold_minutes": 15,
  "allow_waitlist": true
}
```

Ejemplo HotelChat futuro:

```json
{
  "check_in_time": "15:00",
  "check_out_time": "11:00",
  "allow_partial_payment": true
}
```

## 7. Admin web multi-solución

La consola admin debe tener:

- shell común;
- navegación común;
- módulos por solución activa;
- permisos por tenant;
- permisos por solución futura.

Ejemplo:

```text
Admin Shell
├── Dashboard platform
├── Settings
├── Users
├── MediChat module
├── RestoChat module futuro
├── HotelChat module futuro
├── StayChat module futuro
└── StoreChat module futuro
```

## 8. Agente conversacional multi-solución

El agente debe resolver:

1. Tenant.
2. Solución activa.
3. Canal.
4. Estado conversacional.
5. Dominio de herramientas.

Ejemplo MediChat:

```text
tenant = consultorio_ana
solution = medichat
agent = MediChatBookingAgent
tools = medichat tools
```

Ejemplo futuro RestoChat:

```text
tenant = restaurante_xyz
solution = restochat
agent = RestoChatReservationAgent
tools = restochat tools
```

## 9. Tools por solución

Herramientas comunes:

```text
send_message
get_tenant_settings
handoff_to_human
create_payment_attempt
submit_payment_evidence
```

Herramientas MediChat:

```text
search_health_services
get_medichat_available_slots
create_medichat_booking
confirm_medichat_booking
cancel_medichat_booking
```

Herramientas RestoChat futuras:

```text
get_available_tables
create_table_reservation
join_waitlist
```

No mezclar tools de verticales.

## 10. Eventos por solución

Eventos comunes:

```text
payment.created
payment.paid
notification.sent
conversation.started
```

Eventos MediChat:

```text
medichat.booking.created
medichat.booking.confirmed
medichat.appointment.reminder_due
```

Eventos RestoChat futuros:

```text
restochat.reservation.created
restochat.reservation.confirmed
```

## 11. Migraciones por solución

Cada solución debe tener migraciones propias.

Ejemplo:

```text
solutions/medichat/migrations/
solutions/restochat/migrations/
```

Las migraciones de tenant deben aplicar:

1. Migraciones core tenant.
2. Migraciones de soluciones activas.

Para MVP:

```text
core tenant migrations
+
medichat migrations
```

## 12. Regla de promoción a core

Una funcionalidad solo debe promoverse a `packages/` si cumple al menos una condición:

1. Es técnica y no depende de dominio vertical.
2. Será usada por más de un vertical.
3. Es una interfaz común necesaria para providers.
4. Es infraestructura transversal.

Ejemplo que sí puede ir a core:

```text
PaymentProvider
```

Ejemplo que no debe ir a core:

```text
payer_plan de medicina prepagada
```

Aunque “pagador” pueda parecer genérico, la jerarquía EPS/póliza/prepagada pertenece inicialmente a MediChat. Solo se generalizará si otro vertical requiere una estructura equivalente.

## 13. Reglas para nombres de carpetas

Usar minúsculas sin guiones para verticales:

```text
medichat
restochat
hotelchat
staychat
storechat
```

Usar snake_case para módulos Python.

Usar kebab-case para carpetas de specs:

```text
003-medichat-booking-domain
```

## 14. Reglas para documentación

Cada solución debe tener:

```text
solutions/<solution>/README.md
solutions/<solution>/docs/CONCEPTS.md
solutions/<solution>/docs/ROADMAP.md
solutions/<solution>/specs/
```

En etapa inicial se puede mantener documentación central, pero se debe marcar qué secciones son platform y cuáles son MediChat.

## 15. Aplicación al estado actual

La documentación existente de citas médicas debe reinterpretarse así:

```text
TotalChat Platform = base común
MediChat = dominio médico ya especificado
```

Por tanto:

- pacientes = MediChat;
- profesionales de salud = MediChat;
- especialidades = MediChat;
- pólizas/EPS/prepagada = MediChat;
- Docplanner = adaptador relevante inicialmente para MediChat;
- pagos, canales, agenda provider y reuniones = capacidades de plataforma/core.

## 16. Campañas por solución

El módulo de campañas es transversal, pero cada vertical puede aportar resolvers de audiencia.

Ejemplo MediChat:

```text
MediChatAudienceResolver
```

Ejemplo futuro RestoChat:

```text
RestoChatAudienceResolver
```

Regla:

```text
packages/campaigns contiene la lógica común.
solutions/<vertical>/campaigns contiene la lógica específica de audiencia.
```



---

# CAMPAIGNS_AND_BROADCASTS.md
# Campañas, comunicados y mensajería masiva en TotalChat

## 1. Propósito

Este documento define el módulo transversal de **campañas, comunicados y mensajería masiva** de TotalChat.

La necesidad principal es permitir que cada tenant pueda enviar mensajes a sus contactos, clientes, pacientes o usuarios finales desde la consola administrativa, ya sea de forma inmediata o programada.

Este módulo aplica a todos los verticales:

```text
MediChat   → pacientes
RestoChat  → clientes/comensales
HotelChat  → huéspedes
StayChat   → huéspedes/visitantes
StoreChat  → clientes/compradores
```

La primera implementación práctica se hará sobre MediChat, pero el diseño debe ser de plataforma/core, no exclusivo del dominio médico.

## 2. Decisión principal

TotalChat debe incluir un módulo transversal llamado:

```text
Campañas y comunicados
```

Nombre técnico sugerido:

```text
Campaigns / Broadcast Messaging
```

Ubicación técnica recomendada:

```text
packages/campaigns/
```

Este paquete debe integrarse con:

```text
packages/channels/
packages/notifications/
packages/conversations/
packages/events/
packages/tenancy/
solutions/<vertical>/
```

## 3. Casos de uso

### 3.1. Comunicado operativo

Ejemplos:

```text
Este fin de semana no tendremos servicio por temporada de vacaciones.
El lunes festivo no tendremos atención.
La sede Poblado estará cerrada por mantenimiento.
A partir del próximo mes cambiaremos nuestro horario de atención.
```

### 3.2. Campaña publicitaria o promocional

Ejemplos:

```text
Durante agosto tendremos tarifa especial en consulta inicial.
Reserva tu control preventivo este mes.
Nuevo menú de temporada disponible este fin de semana.
Promoción especial para clientes frecuentes.
```

### 3.3. Aviso de agenda o disponibilidad

Ejemplos:

```text
Ya abrimos agenda para septiembre.
Tenemos nuevos horarios disponibles los sábados.
Hay cupos disponibles esta semana.
```

### 3.4. Recordatorio masivo no transaccional

Ejemplos:

```text
Recuerda actualizar tus datos antes de tu próxima cita.
Recuerda confirmar tus datos de contacto.
```

### 3.5. Comunicación segmentada

Ejemplos MediChat:

```text
Enviar comunicado solo a pacientes de la Dra. Ana.
Enviar aviso solo a pacientes con citas futuras.
Enviar promoción solo a pacientes que aceptaron mensajes de marketing.
```

Ejemplos RestoChat:

```text
Enviar campaña a clientes que han reservado los fines de semana.
Enviar aviso de menú especial a clientes frecuentes.
```

Ejemplos StoreChat:

```text
Enviar promoción a clientes interesados en una categoría.
Enviar aviso a clientes con compras anteriores.
```

## 4. Principios rectores

1. El módulo es transversal de TotalChat Platform.
2. No debe vivir exclusivamente en MediChat.
3. Debe respetar consentimiento y preferencias de contacto.
4. Debe respetar políticas de cada canal.
5. Debe registrar auditoría completa.
6. Debe registrar entregas individuales.
7. Debe soportar envío inmediato y programado.
8. Debe soportar segmentación.
9. Debe poder operar inicialmente con Telegram.
10. Debe quedar preparado para WhatsApp, email y otros canales.
11. n8n puede participar como automatizador o dispatcher, pero no como fuente de verdad.
12. No debe enviar mensajes publicitarios a contactos sin consentimiento de marketing.

## 5. Tipos de mensajes

## 5.1. Transactional

Mensajes transaccionales relacionados con una acción específica.

Ejemplos:

```text
Tu cita fue confirmada.
Tu pago está pendiente de revisión.
Tu reserva fue cancelada.
```

Normalmente no son campañas.

## 5.2. Operational

Mensajes operativos o de servicio.

Ejemplos:

```text
No tendremos atención este fin de semana.
La sede estará cerrada por mantenimiento.
El horario cambiará temporalmente.
```

Pueden enviarse a usuarios relacionados con el servicio, respetando políticas de canal y opt-out aplicable.

## 5.3. Marketing

Mensajes publicitarios, promocionales o comerciales.

Ejemplos:

```text
Tenemos una promoción especial este mes.
Conoce nuestro nuevo servicio.
Reserva con descuento.
```

Requieren consentimiento explícito o al menos preferencia habilitada según el marco legal y política del canal.

## 6. Tipos de campaña

Campo sugerido:

```text
campaign_type
```

Valores:

```text
announcement
marketing
schedule_notice
service_notice
reminder_campaign
custom
```

### 6.1. announcement

Comunicado general.

### 6.2. marketing

Campaña publicitaria o promocional.

### 6.3. schedule_notice

Aviso sobre agenda, horarios, cierres o disponibilidad.

### 6.4. service_notice

Aviso sobre servicios.

### 6.5. reminder_campaign

Recordatorio masivo no ligado a una única transacción.

### 6.6. custom

Uso personalizado.

## 7. Modos de envío

Campo sugerido:

```text
send_mode
```

Valores:

```text
send_now
scheduled
```

### 7.1. send_now

La campaña se envía inmediatamente después de confirmación administrativa.

### 7.2. scheduled

La campaña queda programada para una fecha y hora.

Debe considerar:

- timezone del tenant;
- posibilidad de cancelar antes del envío;
- estado `scheduled`;
- worker o scheduler interno;
- idempotencia para no duplicar envíos.

## 8. Estados de campaña

Campo sugerido:

```text
status
```

Estados:

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

## 9. Significado de estados

### 9.1. draft

Campaña en edición.

No se envía.

### 9.2. ready

Campaña lista para enviar, pero aún no enviada ni programada.

### 9.3. scheduled

Campaña programada para fecha futura.

### 9.4. queued

Campaña encolada para procesamiento.

### 9.5. sending

Campaña en proceso de envío.

### 9.6. sent

Todos los destinatarios elegibles fueron procesados exitosamente o con estados finales aceptables.

### 9.7. partially_sent

Algunos envíos fueron exitosos y otros fallaron.

### 9.8. failed

La campaña falló de forma general.

### 9.9. cancelled

Campaña cancelada antes o durante el envío.

### 9.10. paused

Campaña pausada manualmente.

### 9.11. requires_approval

Campaña requiere aprobación antes de enviarse.

### 9.12. approved

Campaña aprobada.

### 9.13. rejected

Campaña rechazada por un aprobador/admin.

## 10. Estados de entrega individual

Campo sugerido:

```text
delivery_status
```

Estados:

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

### 10.1. pending

Entrega creada, no procesada.

### 10.2. queued

Entrega en cola.

### 10.3. skipped

Entrega omitida por regla válida.

### 10.4. sending

Entrega en proceso.

### 10.5. sent

Mensaje enviado al proveedor.

### 10.6. delivered

Proveedor reportó entrega, si el canal lo permite.

### 10.7. read

Proveedor reportó lectura, si el canal lo permite.

### 10.8. failed

Falló el envío.

### 10.9. cancelled

Entrega cancelada.

### 10.10. blocked_by_consent

No se envió por falta de consentimiento.

### 10.11. blocked_by_channel_policy

No se envió por política del canal.

### 10.12. blocked_by_missing_contact

No se envió porque no existe contacto válido en el canal.

## 11. Audiencias

El módulo debe permitir definir una audiencia.

Campo sugerido:

```text
audience_type
```

Valores iniciales:

```text
all_contacts
all_active_contacts
all_patients
all_active_patients
patients_with_future_bookings
patients_with_past_bookings
patients_by_practitioner
patients_by_service
patients_by_location
contacts_by_channel
custom_filter
manual_selection
```

Los valores específicos de MediChat pueden mapearse a pacientes.

Los futuros verticales tendrán sus propios resolvers.

## 12. Segmentación por vertical

## 12.1. MediChat

Segmentos útiles:

```text
todos los pacientes activos
pacientes de un profesional
pacientes de una sede
pacientes de un servicio
pacientes con citas futuras
pacientes con citas pasadas
pacientes con modalidad virtual
pacientes con consentimiento marketing
pacientes con canal Telegram
pacientes con canal WhatsApp
```

## 12.2. RestoChat futuro

Segmentos útiles:

```text
clientes activos
clientes frecuentes
clientes con reservas pasadas
clientes con reservas futuras
clientes que reservaron fin de semana
clientes con cumpleaños próximo
clientes en lista de espera
```

## 12.3. HotelChat futuro

Segmentos útiles:

```text
huéspedes activos
huéspedes con reservas futuras
huéspedes anteriores
huéspedes frecuentes
huéspedes por temporada
huéspedes por tipo de habitación
```

## 12.4. StayChat futuro

Segmentos útiles:

```text
huéspedes anteriores
huéspedes con estadías futuras
huéspedes por propiedad
huéspedes frecuentes
```

## 12.5. StoreChat futuro

Segmentos útiles:

```text
clientes activos
clientes con compras anteriores
clientes por categoría de interés
clientes con carrito abandonado
clientes frecuentes
clientes con consentimiento marketing
```

## 13. Consentimiento y preferencias de contacto

## 13.1. Principio

TotalChat debe respetar consentimiento y preferencias.

No se deben enviar campañas de marketing a contactos sin permiso.

## 13.2. Preferencias mínimas

Por contacto se debe poder registrar:

```text
allow_transactional
allow_operational
allow_marketing
```

También por canal:

```text
telegram
whatsapp
email
sms
```

## 13.3. Opt-out

Todo contacto debe poder quedar excluido de marketing.

Campos:

```text
opted_out_at
opt_out_reason
source
updated_at
```

## 13.4. Diferencia por tipo de mensaje

### Transactional

Usualmente permitido cuando el usuario tiene una relación activa y el mensaje corresponde a una transacción.

### Operational

Permitido bajo política del tenant y del canal, especialmente cuando afecta servicio contratado o citas/reservas.

### Marketing

Requiere preferencia habilitada.

## 14. Políticas de canal

Cada canal puede tener reglas diferentes.

## 14.1. Telegram

Telegram puede permitir escribir a usuarios que iniciaron conversación con el bot.

Reglas:

- Debe existir `chat_id`.
- Debe existir relación tenant/contacto.
- Debe respetarse opt-out.
- Si el bot fue bloqueado, marcar delivery como failed o blocked.

## 14.2. WhatsApp futuro

WhatsApp Business suele requerir plantillas para iniciar conversaciones fuera de ventana de atención.

Reglas futuras:

- Soportar `message_template_id`.
- Soportar variables de plantilla.
- Soportar idioma.
- Validar si el mensaje requiere template.
- Marcar bloqueo si no hay template válido.
- Respetar opt-out.

## 14.3. Email futuro

Reglas futuras:

- Soportar subject.
- Soportar unsubscribe.
- Respetar opt-out.
- Registrar bounced/failed si aplica.

## 14.4. SMS futuro

Reglas futuras:

- Mensajes cortos.
- Costos por envío.
- Opt-out estricto.

## 15. Relación con n8n

n8n puede ser usado para:

- automatizar envío;
- conectar con servicios externos;
- disparar campañas desde eventos;
- enviar reportes;
- integrarse con CRM.

Pero TotalChat debe ser la fuente de verdad de:

- campaña;
- audiencia;
- destinatarios;
- entregas;
- estados;
- auditoría;
- métricas.

Regla:

```text
n8n puede ejecutar, pero no decidir ni ser la única bitácora.
```

## 16. Arquitectura del módulo

Flujo conceptual:

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
Telegram / WhatsApp / Email / SMS
    ↓
Delivery status update
    ↓
Campaign metrics
```

## 17. Componentes

## 17.1. CampaignService

Responsable de crear, editar, aprobar, programar, cancelar y consultar campañas.

## 17.2. AudienceResolver

Responsable de convertir filtros en destinatarios.

Debe ser extensible por vertical.

Ejemplo:

```text
MediChatAudienceResolver
RestoChatAudienceResolver futuro
HotelChatAudienceResolver futuro
StayChatAudienceResolver futuro
StoreChatAudienceResolver futuro
```

## 17.3. CampaignDeliveryPlanner

Responsable de generar entregas individuales.

## 17.4. CampaignScheduler

Responsable de identificar campañas programadas listas para envío.

## 17.5. CampaignDispatcher

Responsable de procesar entregas.

## 17.6. ChannelProvider

Responsable del envío real por canal.

## 17.7. MetricsAggregator

Responsable de métricas básicas.

## 18. Consola admin

El módulo en consola debe llamarse:

```text
Campañas y comunicados
```

Pantallas mínimas:

```text
Listado de campañas
Crear campaña
Editar borrador
Seleccionar audiencia
Previsualizar audiencia
Previsualizar mensaje
Enviar ahora
Programar envío
Cancelar campaña programada
Ver resultados
Ver errores
Duplicar campaña
```

## 19. Campos mínimos de campaña

```text
name
description
campaign_type
message_type
solution_code nullable
target_channel_policy
audience_type
audience_filters
message_body
send_mode
scheduled_at
timezone
status
created_by
approved_by nullable
```

## 20. Confirmación antes de envío

Antes de enviar, la consola debe mostrar:

```text
nombre de campaña
tipo de mensaje
canal
audiencia estimada
cantidad de destinatarios elegibles
cantidad bloqueada por consentimiento
cantidad bloqueada por falta de canal
mensaje final
fecha/hora de envío
usuario responsable
```

El admin debe confirmar explícitamente.

## 21. Métricas mínimas

```text
total_recipients
eligible_recipients
blocked_by_consent
blocked_by_channel_policy
queued_count
sent_count
delivered_count
read_count
failed_count
skipped_count
cancelled_count
```

No todos los canales reportan delivered/read.

## 22. Modelo de datos

## 22.1. campaigns

```text
id
tenant_id
solution_code nullable
name
description nullable
campaign_type
message_type
status
send_mode
scheduled_at nullable
timezone
message_body
target_channel_policy
audience_type
audience_filters
estimated_recipients
eligible_recipients
blocked_recipients
created_by
approved_by nullable
approved_at nullable
sent_at nullable
cancelled_at nullable
created_at
updated_at
```

## 22.2. campaign_audiences

```text
id
campaign_id
audience_type
filters
estimated_recipients
eligible_recipients
blocked_by_consent
blocked_by_channel_policy
blocked_by_missing_contact
created_at
updated_at
```

## 22.3. campaign_recipients

```text
id
campaign_id
recipient_type
recipient_id
contact_id nullable
display_name nullable
channel_type
channel_address
consent_status
eligibility_status
eligibility_reason nullable
created_at
```

## 22.4. campaign_deliveries

```text
id
campaign_id
campaign_recipient_id
recipient_type
recipient_id
channel_type
channel_address
status
provider_message_id nullable
error_code nullable
error_message nullable
queued_at nullable
sent_at nullable
delivered_at nullable
read_at nullable
failed_at nullable
created_at
updated_at
```

## 22.5. contact_preferences

```text
id
tenant_id
solution_code nullable
contact_type
contact_id
channel_type
allow_transactional
allow_operational
allow_marketing
opted_out_at nullable
opt_out_reason nullable
source
created_at
updated_at
```

## 22.6. campaign_templates

```text
id
tenant_id
solution_code nullable
name
description nullable
campaign_type
message_type
channel_type nullable
body_template
variables
status
created_by
created_at
updated_at
```

## 22.7. campaign_events

```text
id
campaign_id
event_type
previous_status nullable
new_status nullable
actor_type
actor_id nullable
metadata
created_at
```

## 23. API inicial

## 23.1. POST `/api/admin/campaigns`

Crea campaña en borrador.

Request:

```json
{
  "name": "Cierre por vacaciones",
  "description": "Aviso operativo de cierre temporal",
  "campaign_type": "schedule_notice",
  "message_type": "operational",
  "solution_code": "medichat",
  "message_body": "Este fin de semana no tendremos servicio por temporada de vacaciones. Retomaremos atención el martes.",
  "audience_type": "all_active_patients",
  "audience_filters": {},
  "target_channel_policy": {
    "preferred_channels": ["telegram"],
    "fallback_channels": []
  }
}
```

## 23.2. POST `/api/admin/campaigns/{campaign_id}/preview-audience`

Calcula audiencia estimada.

Response:

```json
{
  "data": {
    "estimated_recipients": 120,
    "eligible_recipients": 105,
    "blocked_by_consent": 10,
    "blocked_by_channel_policy": 0,
    "blocked_by_missing_contact": 5
  }
}
```

## 23.3. POST `/api/admin/campaigns/{campaign_id}/schedule`

Programa campaña.

Request:

```json
{
  "scheduled_at": "2026-07-10T08:00:00-05:00",
  "timezone": "America/Bogota"
}
```

## 23.4. POST `/api/admin/campaigns/{campaign_id}/send-now`

Envía inmediatamente.

Debe requerir confirmación explícita:

```json
{
  "confirm_send": true
}
```

## 23.5. POST `/api/admin/campaigns/{campaign_id}/cancel`

Cancela campaña programada o en cola.

## 23.6. GET `/api/admin/campaigns/{campaign_id}/deliveries`

Lista entregas individuales.

## 23.7. GET `/api/admin/campaigns/{campaign_id}/metrics`

Devuelve métricas.

## 24. Reglas de seguridad

1. Solo usuarios autorizados pueden crear campañas.
2. Solo usuarios autorizados pueden enviar.
3. Se debe auditar quién envía.
4. No mostrar datos de otro tenant.
5. No permitir campañas sin tenant.
6. No enviar marketing sin consentimiento.
7. No guardar secretos de canal en campaña.
8. No exponer provider tokens.
9. Validar tamaño del mensaje.
10. Validar límites por tenant.

## 25. Límites y rate limiting

Debe existir capacidad de limitar:

```text
mensajes por minuto
mensajes por hora
campañas por día
destinatarios por campaña
```

Estos límites pueden ser globales, por tenant o por canal.

## 26. Adjuntos

MVP no requiere adjuntos.

Futuro:

```text
image
pdf
file
link preview
```

Si se implementan adjuntos:

- validar tamaño;
- validar tipo;
- usar almacenamiento seguro;
- respetar canal.

## 27. Plantillas

MVP puede usar mensajes libres en Telegram.

Futuro debe soportar plantillas:

- WhatsApp templates;
- plantillas internas;
- variables;
- previsualización.

Ejemplo:

```text
Hola {{first_name}}, este fin de semana no tendremos servicio. Retomaremos el {{return_date}}.
```

## 28. Variables

Variables posibles:

```text
first_name
tenant_name
professional_name
location_name
service_name
return_date
booking_date
```

Las variables disponibles dependen del audience resolver.

## 29. Auditoría

Acciones a auditar:

```text
campaign.created
campaign.updated
campaign.previewed
campaign.scheduled
campaign.approved
campaign.rejected
campaign.send_requested
campaign.sending_started
campaign.sent
campaign.partially_sent
campaign.failed
campaign.cancelled
delivery.sent
delivery.failed
```

## 30. MVP recomendado para MediChat

Primera versión:

```text
crear campaña
tipo announcement / schedule_notice / marketing
audiencia: todos los pacientes activos
audiencia: pacientes por profesional
canal: Telegram
envío inmediato
envío programado
preview de audiencia
registro de entregas
respeto básico de preferencias
métricas básicas
```

Fuera del MVP inicial de campañas:

```text
WhatsApp templates
A/B testing
journeys multietapa
CRM avanzado
email marketing
SMS
adjuntos
aprobaciones complejas
segmentación avanzada
```

## 31. Criterios de aceptación

1. Un admin puede crear campaña.
2. Un admin puede previsualizar audiencia.
3. El sistema calcula elegibles y bloqueados.
4. El admin puede enviar ahora.
5. El admin puede programar campaña.
6. El worker procesa campañas programadas.
7. Cada entrega queda registrada.
8. El sistema respeta opt-out de marketing.
9. El sistema registra errores por destinatario.
10. El sistema muestra métricas básicas.
11. El módulo no depende de MediChat internamente.
12. MediChat provee un audience resolver inicial.
13. n8n no es fuente de verdad.

## 32. Regla final

```text
Campañas y comunicados es una capacidad transversal de TotalChat Platform. Debe funcionar inicialmente con MediChat, pero debe diseñarse para todos los verticales.
```



---

# CONSTITUTION.md  
# Constitución del Proyecto TotalChat

## 1. Propósito

Esta constitución gobierna el desarrollo de TotalChat. Cualquier spec, plan, tarea, pull request o implementación debe respetar estas reglas.

TotalChat será una plataforma conversacional multi-tenant para reservas, iniciando por citas médicas, con backend propio, consola administrativa, PostgreSQL, LangGraph, OpenAI, Telegram, pagos y automatizaciones complementarias.

## 2. Principios no negociables

### 2.1. TotalChat no es solo un bot

TotalChat no debe implementarse como un bot aislado.

Debe ser una plataforma compuesta por:

- Backend de dominio.
- Base de datos.
- Consola administrativa.
- Agente conversacional.
- Canales de mensajería.
- Pagos.
- Automatizaciones complementarias.

El bot es una interfaz conversacional sobre una plataforma de reservas.

### 2.2. PostgreSQL es la fuente de verdad

PostgreSQL será la fuente de verdad para:

- Tenants.
- Organizaciones.
- Sedes.
- Consultorios.
- Profesionales.
- Especialidades.
- Servicios del profesional.
- Tarifas.
- Pacientes.
- Citas.
- Estados de pago.
- Evidencias de pago.
- Revisiones manuales.
- Configuraciones del tenant.
- Conversaciones y mensajes relevantes.
- Documentos semánticos.

Ni el LLM ni n8n son fuente de verdad.

### 2.3. La IA conversa, pero no decide la verdad

La IA puede:

- Entender lenguaje natural.
- Identificar intención.
- Resolver ambigüedades.
- Pedir datos faltantes.
- Presentar servicios.
- Presentar horarios.
- Explicar opciones de pago.
- Guiar la conversación.
- Prevalidar información no crítica, como comprobantes de pago.

La IA no puede inventar ni confirmar:

- Precios.
- Disponibilidad.
- Profesionales.
- Servicios.
- Sedes.
- Consultorios.
- Pagos.
- Citas.
- Links de reunión.
- Reembolsos.
- Estados bancarios.
- Diagnósticos médicos.
- Políticas no configuradas.

Toda acción crítica debe ejecutarse mediante herramientas controladas del backend.

### 2.4. No diagnóstico médico

TotalChat no hará diagnóstico médico.

Puede ayudar administrativamente a reservar citas y orientar dentro de servicios configurados por el tenant, pero no debe afirmar enfermedades, tratamientos, diagnósticos ni decisiones clínicas.

Si el usuario expresa una emergencia, el sistema debe recomendar atención médica inmediata o contacto con servicios de emergencia.

### 2.5. Multi-tenancy desde el inicio

TotalChat debe ser multi-tenant desde el inicio.

Un tenant puede representar:

- Profesional independiente.
- Consultorio privado.
- Médico o especialista particular.
- Clínica.
- Centro médico.
- Organización con varias sedes.
- Organización con varios profesionales.

### 2.6. Schema PostgreSQL por tenant

La arquitectura inicial usará:

- Una aplicación.
- Una base PostgreSQL.
- Schema `public` para control SaaS.
- Un schema PostgreSQL por tenant para datos operativos.

Ejemplo:

```text
public
tenant_dra_ana
tenant_dr_carlos
tenant_clinica_vida
```

El LLM nunca decide qué schema usar. El backend resuelve el tenant y schema antes de ejecutar herramientas.

### 2.7. Consola administrativa obligatoria

La consola administrativa es parte esencial del producto.

Debe permitir que cada tenant gestione:

- Organizaciones.
- Sedes.
- Consultorios.
- Profesionales.
- Especialidades.
- Servicios.
- Tarifas.
- Disponibilidad.
- Citas.
- Pacientes.
- Pagos.
- Links virtuales.
- Políticas.
- Canales.

El bot depende de estos datos para operar.

### 2.8. Deshabilitar antes que eliminar

Para datos maestros y operativos, se debe preferir deshabilitar antes que eliminar.

Aplica a:

- Profesionales.
- Servicios.
- Tarifas.
- Sedes.
- Consultorios.
- Especialidades.
- Pacientes.
- Citas.
- Configuraciones.

### 2.9. La especialidad no define precio

La especialidad clasifica, pero no define precio.

Ejemplos de especialidad:

- Psicología.
- Dermatología.
- Odontología.
- Medicina general.

El precio depende del servicio ofrecido por un profesional y del plan comercial aplicable.

### 2.10. Cada profesional tiene sus propios servicios

Cada profesional define sus propios servicios, duración, modalidad y condiciones.

Dos profesionales de la misma especialidad pueden tener servicios y precios distintos.

### 2.11. Precios por jerarquía comercial flexible

El modelo de precios debe soportar esta jerarquía:

```text
Tipo de pagador
  → Entidad / pagador
    → Plan / producto / convenio
      → Tarifa específica del servicio del profesional
```

Ejemplos:

```text
Particular
  → Particular
    → Tarifa particular

Medicina prepagada
  → Sura
    → Póliza básica
    → Póliza mejorada

Medicina prepagada
  → Colsanitas
    → Plan inicial
    → Plan avanzado

Póliza de salud
  → Aseguradora ABC
    → Plan pequeño
```

El precio final debe configurarse por:

```text
practitioner_service + payer_plan
```

No por tipo general únicamente.

### 2.12. La cita guarda snapshot

Toda cita debe guardar snapshot de:

- Servicio.
- Profesional.
- Duración.
- Modalidad.
- Sede.
- Consultorio.
- Dirección.
- Tipo de pagador.
- Entidad/pagador.
- Plan.
- Precio.
- Moneda.
- Total.

Esto evita que cambios futuros de tarifas modifiquen citas existentes.

### 2.13. Paciente previo no es requisito

El usuario no necesita existir previamente como paciente para reservar.

El bot debe pedir datos mínimos y crear un paciente incompleto si es necesario.

Los datos adicionales se completan antes de la cita, desde la consola administrativa o mediante flujos posteriores.

### 2.14. Datos mínimos configurables

Cada tenant puede configurar qué datos son obligatorios y en qué etapa:

- before_booking
- before_payment
- before_confirmation
- before_appointment
- before_invoice
- at_reception

Por defecto, la reserva debe requerir la mínima información viable.

### 2.15. Citas presenciales y virtuales

TotalChat debe soportar:

- Presencial.
- Virtual.
- Ambas.

El MVP debe permitir links virtuales manuales. La generación automática con Teams, Google Meet, Zoom u otros proveedores será futura.

### 2.16. OpenAI inicial, arquitectura desacoplada

OpenAI será el proveedor LLM inicial.

Debe existir una abstracción `LLMProvider`.

Ollama o modelos locales podrán ser evaluados en laboratorio o fases futuras, pero no son dependencia crítica del MVP.

### 2.17. pgvector desde el inicio

TotalChat usará pgvector desde el inicio para búsqueda semántica sobre:

- Servicios.
- Especialidades.
- Preguntas frecuentes.
- Políticas.
- Instrucciones de pago.
- Instrucciones de llegada.
- Instrucciones de citas virtuales.

pgvector no determina disponibilidad, precio ni pago.

### 2.18. Redis recomendado desde el MVP

Redis podrá usarse para:

- Estado temporal de conversación.
- Holds temporales de slots.
- Locks para evitar doble reserva.
- Rate limiting.
- Cache ligera.
- Futuras colas.

Redis no es fuente de verdad.

### 2.19. Telegram primero

El primer canal será Telegram directo.

WhatsApp se implementará después.

### 2.20. Pagos simulados primero, Wompi después

El MVP usará pagos simulados y flujos manuales.

Wompi se implementará después en sandbox.

### 2.21. Transferencias con revisión humana

Para transferencias:

- El sistema espera evidencia de pago por un tiempo configurable.
- Si no se envía evidencia, la reserva expira y el horario se libera.
- Si se envía evidencia, la reserva queda protegida y pasa a revisión manual.
- La falta de revisión administrativa no debe liberar la reserva salvo configuración explícita.
- Revisión vencida genera alertas y escalamiento.

La IA puede prevalidar comprobantes, pero no confirmar pagos.

### 2.22. Pasarela confirmada puede confirmar automáticamente

Pagos por Wompi u otra pasarela pueden confirmar automáticamente cuando haya webhook/evento confiable validado.

### 2.23. Pago en sitio configurable

Cada tenant define si acepta pago en sitio.

Algunos profesionales pueden requerir pago previo para evitar no-show.

### 2.24. Recordatorios y confirmación de asistencia

TotalChat debe soportar recordatorios por el mismo canal del usuario.

Si el usuario confirma asistencia, la cita se mantiene.

Si responde que no asistirá, se debe pedir una segunda confirmación, advirtiendo:

- El cupo será liberado.
- Una nueva cita dependerá de disponibilidad.
- Si ya pagó, el reembolso se hará según política configurable.

La cancelación por falta de respuesta es configurable, no obligatoria.

### 2.25. n8n complementario

n8n puede enviar recordatorios, alertas, encuestas y notificaciones.

n8n no debe contener la lógica principal de reservas, pagos, disponibilidad, estado de citas o multi-tenancy.

## 3. Reglas de no desviación

1. No convertir TotalChat en historia clínica.
2. No implementar diagnóstico médico.
3. No construir carrito/POS en el MVP.
4. No implementar restaurantes antes del MVP médico.
5. No implementar hoteles antes de analizar brechas.
6. No usar n8n como core.
7. No permitir que la IA invente datos críticos.
8. No permitir que la IA elija tenant/schema.
9. No usar tenant_id como único aislamiento principal.
10. No asumir precio único por especialidad.
11. No asumir precio único por servicio del profesional.
12. No limitar precios a solo particular/prepagada/póliza.
13. No confirmar transferencias automáticamente por imagen.
14. No liberar reserva por revisión administrativa vencida salvo configuración explícita.
15. No cancelar por respuesta negativa sin segunda confirmación.
16. No cancelar por falta de respuesta salvo política explícita.
17. No implementar salas automáticas antes de links manuales.
18. No implementar Wompi antes de pagos simulados.
19. No implementar WhatsApp antes de Telegram.
20. No guardar secretos en el repositorio.
21. No eliminar físicamente datos maestros por defecto.
22. No acoplar el código directamente a OpenAI.
23. No usar Redis como fuente de verdad.
24. No usar pgvector para datos transaccionales críticos.

## 2.26. Integraciones externas de agenda y calendario

TotalChat debe tener motor interno de agenda y reservas, pero la arquitectura debe permitir configurar proveedores externos de agenda/calendario por tenant, organización o profesional.

Docplanner, Google Calendar, Microsoft Calendar y otros sistemas deben implementarse como adaptadores mediante una capa genérica de proveedores, no como dependencias del core.

Reglas:

- TotalChat puede operar con agenda interna sin depender de terceros.
- Un tenant puede configurar una agenda externa como autoridad de disponibilidad.
- Para tenants con agenda externa como autoridad, TotalChat no debe confirmar localmente una cita sin validar, crear o bloquear primero la reserva en el proveedor externo.
- La integración externa no reemplaza pagos, precios, revisión manual, recordatorios, confirmación de asistencia, conversación, consola administrativa ni multi-tenancy.
- Docplanner debe ser una implementación de `SchedulingProvider`, no el diseño completo.
- Google Calendar y Microsoft Calendar deben ser adaptadores equivalentes en la misma capa.

## 2.27. Separación entre agenda y reunión virtual

TotalChat debe separar proveedor de agenda de proveedor de reunión virtual.

- `SchedulingProvider` maneja disponibilidad, reservas, cancelaciones, reprogramaciones y bloqueos.
- `MeetingProvider` maneja links de reunión virtual.

Ejemplos:

- Docplanner puede ser `SchedulingProvider`.
- Google Calendar puede ser `SchedulingProvider`.
- Microsoft Calendar puede ser `SchedulingProvider`.
- Google Meet puede ser `MeetingProvider`.
- Microsoft Teams puede ser `MeetingProvider`.
- Link manual será `ManualMeetingProvider` en MVP.

## 3. Reglas adicionales de no desviación sobre agendas externas

25. No crear un conector rígido exclusivo a Docplanner como parte del core.
26. No hacer que Docplanner sea requisito para operar TotalChat.
27. No mezclar agenda externa y reuniones virtuales en una sola abstracción rígida.
28. No confirmar citas locales para tenants con agenda externa autoritativa sin validación/reserva externa.
29. No reducir el modelo de precios jerárquico de TotalChat para ajustarlo a las limitaciones de Docplanner, Google Calendar o Microsoft.
30. No delegar pagos, revisión manual de transferencias o políticas comerciales a proveedores de calendario.


### 2.26. Estados críticos gobernados por máquinas de estado

Los estados de citas, pagos, evidencias, revisiones, confirmación de asistencia, reembolsos, citas virtuales e integraciones externas no deben modificarse libremente desde controladores o handlers.

Toda transición crítica debe pasar por servicios de dominio y respetar `docs/STATE_MACHINES.md`.

Reglas:

- No cambiar estados críticos con updates directos sin validar transición.
- No confirmar citas saltándose reglas de pago y agenda.
- No marcar pagos como aprobados sin revisión o confirmación válida.
- No cancelar por respuesta negativa sin segunda confirmación.
- No liberar slots protegidos por evidencia enviada salvo configuración explícita.

### 2.27. TotalChat como plataforma paraguas y MediChat como primer vertical

TotalChat debe entenderse como plataforma paraguas y familia de soluciones, no como el nombre exclusivo del producto médico.

Nombres oficiales:

```text
TotalChat  = plataforma paraguas
MediChat   = médicos y profesionales de salud
RestoChat  = restaurantes y bares
HotelChat  = hoteles
StayChat   = Airbnb y otros alojamientos
StoreChat  = tiendas y comercio minorista
```

El primer vertical implementado será MediChat.

Reglas:

- TotalChat Core no debe contener reglas médicas.
- MediChat debe contener el dominio médico.
- RestoChat, HotelChat, StayChat y StoreChat quedan como verticales futuros.
- Nuevos verticales deben implementarse dentro de `solutions/`.
- Funcionalidad común solo debe promoverse a `packages/` si es realmente reusable.

### 2.28. Política de repositorio monorepo modular

TotalChat iniciará como monorepo modular.

Estructura conceptual:

```text
apps/
packages/
solutions/
docs/
specs/
infra/
scripts/
tests/
```

Reglas:

- `packages/` contiene capacidades compartidas.
- `solutions/medichat/` contiene dominio médico.
- El core no importa soluciones.
- Las soluciones pueden importar packages.
- Las soluciones no deben importarse entre sí.
- Codex no debe mezclar lógica médica en core.
- Separación futura en repos independientes solo debe hacerse cuando el core y los verticales estén maduros.

### 2.29. Campañas, comunicados y mensajería masiva

TotalChat debe soportar campañas, comunicados y mensajería masiva como capacidad transversal de plataforma, reutilizable por todos los verticales.

Esta capacidad debe permitir:

- crear campañas desde consola admin;
- enviar mensajes inmediatos;
- programar mensajes;
- segmentar audiencias;
- respetar preferencias de contacto;
- respetar consentimiento;
- registrar auditoría;
- registrar entregas individuales;
- medir resultados básicos;
- usar canales configurados como Telegram o WhatsApp futuro.

Reglas:

- Campañas y comunicados no deben ser exclusivos de MediChat.
- Marketing no debe enviarse a contactos sin consentimiento.
- n8n puede ejecutar o complementar, pero no debe ser fuente de verdad.
- El admin debe confirmar explícitamente antes de enviar una campaña.
- Se deben respetar políticas del canal.



---

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

El código no debe llamar directamente a OpenAI desde cualquier módulo.

Debe existir:

```text
LLMProvider
OpenAIProvider
```

Futuro:

```text
OllamaProvider
OtherProvider
```

Variables:

```text
TOTALCHAT_LLM_PROVIDER=openai
TOTALCHAT_LLM_MODEL=...
TOTALCHAT_EMBEDDINGS_PROVIDER=openai
TOTALCHAT_EMBEDDINGS_MODEL=...
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



---

# DATA_MODEL.md  
# Modelo de Datos Conceptual de TotalChat

## 1. Principio general

TotalChat usará PostgreSQL con:

- Schema `public` para control SaaS.
- Un schema por tenant para datos operativos.
- pgvector para búsqueda semántica.

El modelo prioriza:

- Multi-tenancy.
- Flexibilidad comercial.
- Snapshot histórico.
- Auditoría.
- Seguridad.
- Evolución futura.

---

# 2. Schema public

## 2.1. tenants

Representa cada cliente de TotalChat.

Campos conceptuales:

```text
id
name
slug
schema_name
status
plan_id
created_at
updated_at
```

## 2.2. tenant_channels

Canales configurados por tenant.

```text
id
tenant_id
channel_type
external_identifier
webhook_secret_hash
settings
is_active
created_at
updated_at
```

`channel_type`:

```text
telegram
whatsapp
web
```

## 2.3. tenant_domains

Dominios o subdominios del tenant.

```text
id
tenant_id
domain
is_primary
status
```

## 2.4. users

Usuarios administrativos.

```text
id
email
password_hash
full_name
status
created_at
updated_at
```

## 2.5. user_tenants

Relación usuario-tenant.

```text
user_id
tenant_id
role
status
```

Roles:

```text
owner
admin
staff
readonly
```

## 2.6. plans / subscriptions

Para futuro manejo SaaS.

```text
plans
subscriptions
```

---

# 3. Schema tenant

Cada tenant tiene su propio schema.

Ejemplo:

```text
tenant_dra_ana
tenant_clinica_vida
```

---

# 4. Organizaciones y ubicaciones

## 4.1. organizations

```text
id
name
organization_type
legal_name
tax_id
email
phone
status
created_at
updated_at
```

`organization_type`:

```text
independent_practitioner
clinic
health_center
office
other
```

## 4.2. locations

```text
id
organization_id
name
address
city
neighborhood
reference
is_virtual
status
created_at
updated_at
```

## 4.3. rooms

```text
id
location_id
name
room_type
capacity
status
created_at
updated_at
```

---

# 5. Profesionales y especialidades

## 5.1. practitioners

```text
id
full_name
professional_type
professional_license
email
phone
status
created_at
updated_at
```

## 5.2. organization_practitioners

```text
organization_id
practitioner_id
role
status
```

## 5.3. specialties

```text
id
name
description
status
```

## 5.4. practitioner_specialties

```text
practitioner_id
specialty_id
status
```

---

# 6. Servicios

## 6.1. service_catalog

Catálogo opcional de referencia, sin precio obligatorio.

```text
id
name
description
specialty_id
status
```

## 6.2. practitioner_services

Entidad central de lo reservable.

```text
id
organization_id
practitioner_id
service_catalog_id nullable
name
description
duration_minutes
requires_payment
status
created_at
updated_at
```

No debe tener precio único rígido.

## 6.3. service_modalities

```text
id
practitioner_service_id
modality
location_id nullable
room_id nullable
status
```

`modality`:

```text
in_person
virtual
both
```

---

# 7. Precios y condiciones comerciales

## 7.1. Modelo jerárquico

El precio se basa en:

```text
payer_type → payer → payer_plan → practitioner_service_price
```

Ejemplo:

```text
Particular
  → Particular
    → Tarifa particular

Medicina prepagada
  → Sura
    → Póliza básica
    → Póliza mejorada

Medicina prepagada
  → Colsanitas
    → Plan inicial
    → Plan avanzado

Póliza de salud
  → Aseguradora ABC
    → Plan pequeño
```

## 7.2. payer_types

```text
id
code
name
description
status
```

Ejemplos:

```text
particular
eps
medicina_prepagada
poliza_salud
convenio_empresarial
otro
```

## 7.3. payers

```text
id
payer_type_id
name
description
status
```

Ejemplos:

```text
Particular
Sura
Colsanitas
Aseguradora ABC
Nueva EPS
Empresa XYZ
```

## 7.4. payer_plans

```text
id
payer_id
name
description
status
```

Ejemplos:

```text
Tarifa particular
Póliza básica
Póliza mejorada
Plan inicial
Plan avanzado
Plan pequeño
```

## 7.5. practitioner_service_prices

Precio específico por servicio del profesional y plan.

```text
id
practitioner_service_id
payer_plan_id
price
currency
valid_from
valid_to
status
```

## 7.6. patient_payer_profiles

Planes o coberturas declaradas/asociadas al paciente.

```text
id
patient_id
payer_plan_id
member_id nullable
status
validation_status
valid_from
valid_to
created_at
updated_at
```

`validation_status`:

```text
declared
pending_validation
validated
rejected
expired
```

---

# 8. Pacientes

## 8.1. patients

```text
id
full_name
phone nullable
email nullable
document_type nullable
document_number nullable
profile_status
created_from_channel
created_at
updated_at
```

`profile_status`:

```text
minimal
incomplete
complete
verified
inactive
```

## 8.2. patient_contacts

```text
id
patient_id
channel_type
value
external_id nullable
is_primary
is_verified
status
```

## 8.3. required_patient_fields

Configuración por tenant de datos obligatorios por etapa.

```text
id
field_code
required_stage
is_required
status
```

`required_stage`:

```text
before_booking
before_payment
before_confirmation
before_appointment
before_invoice
at_reception
```

---

# 9. Disponibilidad

## 9.1. availability_rules

```text
id
organization_id
practitioner_id
practitioner_service_id nullable
location_id nullable
room_id nullable
modality
weekday
start_time
end_time
valid_from
valid_to
buffer_minutes
status
```

## 9.2. availability_exceptions

```text
id
practitioner_id
location_id nullable
room_id nullable
starts_at
ends_at
exception_type
reason
status
```

`exception_type`:

```text
vacation
sick_leave
administrative_block
special_schedule
holiday
manual_block
```

---

# 10. Citas

## 10.1. bookings

```text
id
organization_id
patient_id
practitioner_id
practitioner_service_id
payer_type_id nullable
payer_id nullable
payer_plan_id nullable
location_id nullable
room_id nullable
modality
starts_at
ends_at
status
payment_status
attendance_confirmation_status
service_name_snapshot
duration_minutes_snapshot
practitioner_name_snapshot
payer_type_name_snapshot nullable
payer_name_snapshot nullable
payer_plan_name_snapshot nullable
price_snapshot
currency_snapshot
total_amount
address_snapshot nullable
room_snapshot nullable
created_channel
pending_patient_data
created_at
updated_at
```

## 10.2. booking_status_history

```text
id
booking_id
previous_status
new_status
changed_by_type
changed_by_id nullable
reason
created_at
```

## 10.3. Estados de cita

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
```

---

# 11. Citas virtuales

## 11.1. booking_virtual_details

```text
id
booking_id
provider
meeting_url
meeting_id
access_code
status
created_mode
created_at
updated_at
```

`provider`:

```text
manual
teams
google_meet
zoom
jitsi
other
```

`status`:

```text
pending
created
sent
cancelled
failed
```

`created_mode`:

```text
manual
automatic
external
```

---

# 12. Pagos

## 12.1. tenant_payment_settings

```text
id
allow_gateway_payment
allow_manual_transfer
allow_pay_at_location
require_payment_before_confirmation
auto_confirm_gateway_payments
require_manual_review_for_transfers
payment_evidence_due_minutes
manual_review_due_policy
manual_review_due_time
manual_review_business_days_only
auto_expire_if_no_evidence
auto_expire_if_review_overdue
refund_policy_days
refund_policy_message
```

## 12.2. payment_attempts

```text
id
booking_id
method
provider
amount_expected
amount_received nullable
currency
status
external_reference nullable
payment_url nullable
expires_at nullable
created_at
updated_at
```

`method`:

```text
gateway
manual_transfer
pay_at_location
simulated
```

`status`:

```text
pending
pending_evidence
evidence_uploaded
pending_manual_review
review_overdue
approved
rejected
paid
failed
expired_no_evidence
expired
pay_at_location
```

## 12.3. payment_evidence

```text
id
payment_attempt_id
file_url
file_type
uploaded_by
uploaded_at
ai_extracted_data
ai_prevalidation_status
ai_prevalidation_notes
```

## 12.4. payment_reviews

```text
id
payment_attempt_id
reviewed_by
reviewed_at
decision
notes
confirmed_against_bank
previous_status
new_status
```

`decision`:

```text
approved
rejected
needs_more_evidence
```

## 12.5. refunds

```text
id
booking_id
payment_attempt_id
amount
currency
status
reason
due_days
processed_at
notes
```

---

# 13. Recordatorios

## 13.1. appointment_confirmation_settings

```text
id
enabled
reminder_hours_before
require_attendance_confirmation
second_confirmation_on_negative_response
no_response_policy
no_response_deadline_hours_before
auto_cancel_on_no_response
refund_policy_days
refund_policy_message
```

`no_response_policy`:

```text
mark_unconfirmed
send_second_reminder
notify_admin
auto_cancel
```

---

# 14. Conversaciones

## 14.1. conversation_sessions

```text
id
channel_type
external_user_id
patient_id nullable
booking_id nullable
status
state
created_at
updated_at
```

## 14.2. messages

```text
id
conversation_session_id
direction
message_type
content
raw_payload
intent nullable
tool_calls nullable
created_at
```

---

# 15. Semántica y pgvector

## 15.1. semantic_documents

```text
id
source_type
source_id
content
metadata
embedding
embedding_provider
embedding_model
embedding_version
status
created_at
updated_at
```

Usos:

- Servicios.
- Especialidades.
- FAQ.
- Políticas.
- Instrucciones.

---

# 16. Eventos

## 16.1. domain_events

```text
id
event_type
aggregate_type
aggregate_id
payload
status
created_at
processed_at nullable
```

Ejemplos:

```text
booking.created
booking.confirmed
payment.evidence_uploaded
payment.review_overdue
reminder.due
attendance.confirmed
attendance.declined
virtual_link.pending
```

# 17. Integraciones externas de agenda, calendario y reuniones

## 17.1. external_systems

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

## 17.2. scheduling_provider_configs

Define el proveedor de agenda activo por tenant, organización o profesional.

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

## 17.3. meeting_provider_configs

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

## 17.4. external_practitioner_mappings

```text
id
practitioner_id
external_system_id
external_practitioner_id
raw_external_payload
status
last_synced_at
```

## 17.5. external_location_mappings

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

## 17.6. external_service_mappings

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

## 17.7. external_booking_mappings

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

## 17.8. external_events

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

## 17.9. external_sync_runs

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

# Modelo multi-solución en public schema

TotalChat debe reconocer que un tenant puede tener una o varias soluciones activas.

## solutions

```text
id
code
name
description
status
created_at
updated_at
```

Códigos oficiales iniciales:

```text
medichat
restochat
hotelchat
staychat
storechat
```

## tenant_solutions

```text
id
tenant_id
solution_id
status
settings
created_at
updated_at
```

Para MVP:

```text
tenant_solutions = medichat
```

Futuro:

Un mismo tenant podría tener más de una solución.

Ejemplo:

```text
Tenant Club Campestre
├── RestoChat
├── HotelChat
└── StayChat
```

## Regla de datos por vertical

El dominio médico documentado actualmente pertenece a MediChat.

Por tanto:

- patients = MediChat;
- practitioners = MediChat;
- specialties = MediChat;
- payer_types/payers/payer_plans de salud = MediChat;
- appointments/bookings médicos = MediChat.

Las capacidades comunes como pagos, conversaciones, canales, providers y eventos pueden vivir en platform/core.

# Modelo de campañas y comunicados

El módulo de campañas debe ser transversal.

Tablas principales:

```text
campaigns
campaign_audiences
campaign_recipients
campaign_deliveries
contact_preferences
campaign_templates
campaign_events
```

## campaigns

```text
id
tenant_id
solution_code nullable
name
description nullable
campaign_type
message_type
status
send_mode
scheduled_at nullable
timezone
message_body
target_channel_policy
audience_type
audience_filters
estimated_recipients
eligible_recipients
blocked_recipients
created_by
approved_by nullable
approved_at nullable
sent_at nullable
cancelled_at nullable
created_at
updated_at
```

## contact_preferences

```text
id
tenant_id
solution_code nullable
contact_type
contact_id
channel_type
allow_transactional
allow_operational
allow_marketing
opted_out_at nullable
opt_out_reason nullable
source
created_at
updated_at
```

Regla:

Los mensajes de marketing requieren `allow_marketing=true`.



---

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
  "document_type": null,
  "document_number": null,
  "created_from_channel": "admin"
}
```

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
- Si faltan datos no críticos, `profile_status` puede ser `minimal` o `incomplete`.

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
  "weekday": 1,
  "start_time": "08:00",
  "end_time": "12:00",
  "valid_from": "2026-07-01",
  "valid_to": null,
  "buffer_minutes": 0
}
```

Reglas:

- `weekday`: 1 lunes, 7 domingo, o el estándar que se defina en implementación; debe documentarse.
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

## 15. Pagos

### 15.1. GET `/api/admin/payment-settings`

### 15.2. PATCH `/api/admin/payment-settings`

Request:

```json
{
  "allow_gateway_payment": false,
  "allow_manual_transfer": true,
  "allow_pay_at_location": false,
  "require_payment_before_confirmation": true,
  "payment_evidence_due_minutes": 60,
  "manual_review_due_policy": "next_business_day_noon",
  "auto_expire_if_no_evidence": true,
  "auto_expire_if_review_overdue": false,
  "refund_policy_days": 5
}
```

### 15.3. POST `/api/admin/bookings/{booking_id}/payment-attempts`

Request transferencia:

```json
{
  "method": "manual_transfer",
  "amount_expected": 100000,
  "currency": "COP"
}
```

Response:

```json
{
  "data": {
    "id": "uuid",
    "method": "manual_transfer",
    "status": "pending_evidence",
    "evidence_due_at": "2026-07-05T18:00:00-05:00"
  }
}
```

### 15.4. POST `/api/admin/payment-attempts/{payment_attempt_id}/evidence`

Request conceptual:

```json
{
  "file_url": "s3://bucket/evidence.png",
  "file_type": "image/png",
  "uploaded_by": "patient"
}
```

Reglas:

- Al cargar evidencia, booking pasa a `pending_manual_payment_review`.
- El slot queda protegido.
- IA puede prevalidar, pero no aprobar.

### 15.5. POST `/api/admin/payment-attempts/{payment_attempt_id}/reviews`

Request aprobar:

```json
{
  "decision": "approved",
  "notes": "Pago verificado en cuenta bancaria.",
  "confirmed_against_bank": true
}
```

Request rechazar:

```json
{
  "decision": "rejected",
  "notes": "El comprobante no corresponde al valor esperado.",
  "confirmed_against_bank": false
}
```

Reglas:

- `approved` requiere `confirmed_against_bank=true`.
- Aprobación confirma pago.
- Si pago requerido, puede confirmar cita.
- Todo queda auditado.

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
LLMProvider = OpenAIProvider
```

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



---

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

### 4.1. Estados

```text
pending
pending_evidence
evidence_uploaded
pending_manual_review
review_overdue
approved
rejected
paid
failed
expired_no_evidence
expired
pay_at_location
```

### 4.2. Transiciones

```text
pending → pending_evidence
pending → pay_at_location
pending → paid
pending → failed
pending → expired

pending_evidence → evidence_uploaded
pending_evidence → expired_no_evidence
pending_evidence → failed

evidence_uploaded → pending_manual_review
pending_manual_review → approved
pending_manual_review → rejected
pending_manual_review → review_overdue

review_overdue → approved
review_overdue → rejected
review_overdue → pending_manual_review

approved → paid
rejected → pending_evidence
rejected → expired
pay_at_location → paid
pay_at_location → failed
```

### 4.3. Reglas

1. Transferencia manual no pasa a `paid` sin revisión aprobada.
2. `approved` requiere `confirmed_against_bank=true`.
3. IA no produce `approved`.
4. Si `expired_no_evidence`, la cita asociada debe pasar a `expired_no_evidence`.
5. Si `review_overdue`, la cita no se libera automáticamente salvo configuración explícita.
6. Si `paid` y la cita requiere pago, la cita puede pasar a `confirmed`.

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



---

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



---

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



---

# PR_REVIEW_CHECKLIST.md
# Checklist de revisión de Pull Requests para TotalChat

## 1. Propósito

Este checklist debe usarse para revisar cada PR generado por Codex o por cualquier desarrollador.

El objetivo es mantener SDD estricto y evitar desviaciones.

## 2. Checklist general

Antes de aprobar un PR, verificar:

```text
[ ] El PR implementa una spec identificada.
[ ] El PR no implementa funcionalidades fuera de la spec activa.
[ ] El PR respeta docs/CONSTITUTION.md.
[ ] El PR actualiza documentación si introduce decisión nueva.
[ ] El PR tiene pruebas relevantes.
[ ] El PR no rompe pruebas existentes.
[ ] El PR no contiene secretos.
[ ] El PR no contiene datos reales de pacientes.
[ ] El PR no introduce dependencias innecesarias.
[ ] El PR tiene migraciones si modifica base de datos.
[ ] El PR tiene manejo de errores.
[ ] El PR tiene logging razonable sin datos sensibles.
```

## 3. Multi-tenancy

```text
[ ] No usa tenant_id como único aislamiento principal.
[ ] Usa schema por tenant.
[ ] No expone schema_name al frontend ni al LLM.
[ ] Resuelve tenant antes de acceder a datos operativos.
[ ] Verifica permisos del usuario sobre el tenant.
[ ] Incluye tests de aislamiento si toca multi-tenancy.
```

## 4. Dominio de citas

```text
[ ] No confirma citas sin validar disponibilidad.
[ ] Guarda snapshot de servicio, profesional, precio, plan y moneda.
[ ] No asume que el paciente debe existir previamente.
[ ] Permite paciente mínimo/incompleto.
[ ] No ignora modalidad presencial/virtual.
[ ] No salta BookingService para cambiar estados directamente.
[ ] Respeta STATE_MACHINES.md.
```

## 5. Precios

```text
[ ] No coloca precio único rígido en practitioner_services.
[ ] Usa jerarquía payer_type → payer → payer_plan.
[ ] El precio se asocia a practitioner_service + payer_plan.
[ ] Particular se modela como plan.
[ ] No inventa precio si no existe tarifa.
[ ] Guarda snapshot de payer_type, payer, payer_plan y price.
```

## 6. Pagos

```text
[ ] No confirma transferencias automáticamente por evidencia.
[ ] La IA solo prevalida comprobantes.
[ ] La aprobación manual exige confirmed_against_bank cuando aplica.
[ ] Si no hay evidencia en plazo, libera slot según política.
[ ] Si hay evidencia, protege slot.
[ ] Review overdue no libera slot por defecto.
[ ] Registra auditoría de revisión.
```

## 7. Recordatorios

```text
[ ] Recordatorio usa canal configurado.
[ ] Respuesta negativa no cancela inmediatamente.
[ ] Pide segunda confirmación.
[ ] Mensaje advierte liberación de cupo y reembolso.
[ ] No respuesta no cancela salvo política explícita.
```

## 8. IA

```text
[ ] No llama OpenAI directamente fuera de LLMProvider.
[ ] No permite que IA elija tenant/schema.
[ ] No permite que IA confirme pagos.
[ ] No permite que IA invente disponibilidad.
[ ] No permite que IA invente precios.
[ ] Tools del agente ejecutan servicios de dominio.
[ ] Se registran tool calls relevantes.
```

## 9. SchedulingProvider / MeetingProvider

```text
[ ] BookingService usa SchedulingProvider o queda preparado para hacerlo.
[ ] No acopla agenda a Docplanner.
[ ] No acopla agenda exclusivamente a implementación interna si la spec requiere abstracción.
[ ] No mezcla MeetingProvider con SchedulingProvider.
[ ] MVP usa InternalSchedulingProvider y ManualMeetingProvider.
[ ] Agenda externa futura no reemplaza pagos/precios/conversación.
```

## 10. Seguridad

```text
[ ] No hay secretos en código.
[ ] No hay tokens en logs.
[ ] Webhooks validan secreto/token.
[ ] Passwords se guardan con hash.
[ ] Endpoints admin requieren auth.
[ ] Acciones críticas quedan auditadas.
```

## 11. Base de datos

```text
[ ] Migraciones son reversibles o tienen estrategia clara.
[ ] Tablas tienen timestamps.
[ ] Tablas críticas tienen status.
[ ] No hay deletes físicos innecesarios.
[ ] Índices razonables para foreign keys y búsquedas principales.
[ ] pgvector se usa solo donde corresponde.
```

## 12. Frontend admin

```text
[ ] Formularios validan campos.
[ ] No muestra datos de otro tenant.
[ ] Maneja errores de API.
[ ] No expone secretos.
[ ] Usa términos consistentes con docs.
```

## 13. Resultado de revisión

Clasificación sugerida:

```text
APPROVE
REQUEST_CHANGES
COMMENT_ONLY
BLOCKED_BY_SCOPE_DEVIATION
BLOCKED_BY_SECURITY
BLOCKED_BY_DATA_MODEL
```

Si el PR se desvía de la spec:

```text
REQUEST_CHANGES: El PR implementa alcance no autorizado. Debe limitarse a la spec activa o documentar una propuesta de desviación para aprobación.
```

## 14. Marca, verticales y repositorio

```text
[ ] El PR respeta TotalChat como plataforma paraguas.
[ ] El PR trata MediChat como primer vertical médico.
[ ] El PR no implementa lógica médica dentro de packages/core.
[ ] El PR no mezcla dominios entre verticales.
[ ] El PR usa packages/ para capacidades compartidas.
[ ] El PR usa solutions/medichat para dominio médico.
[ ] El PR no implementa RestoChat, HotelChat, StayChat o StoreChat si la spec activa no lo pide.
[ ] El PR no introduce repositorios separados sin decisión aprobada.
```

## 15. Campañas y comunicados

```text
[ ] El PR trata campañas como capacidad transversal de plataforma.
[ ] El PR no implementa campañas solo dentro de MediChat.
[ ] El PR respeta consentimiento de marketing.
[ ] El PR registra entregas individuales.
[ ] El PR audita creación, programación, envío y cancelación.
[ ] El PR no usa n8n como fuente de verdad.
[ ] El PR valida políticas de canal.
[ ] El PR evita envíos duplicados.
[ ] El PR soporta idempotencia o estrategia equivalente.
[ ] El PR no permite que IA envíe campañas sin revisión humana.
```



---

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



---

# PAYMENTS.md  
# Modelo de Pagos, Transferencias, Evidencias y Revisión Manual

## 1. Principios

TotalChat debe soportar varios métodos de pago, pero cada uno tiene reglas distintas.

Métodos iniciales:

- Pago simulado.
- Transferencia manual.
- Pago en sitio.
- Pasarela futura Wompi.

## 2. Regla principal

Una transferencia no debe confirmar automáticamente una cita solo por recibir una imagen.

La IA puede prevalidar el comprobante, pero no confirmar recepción real del dinero.

## 3. Métodos

### 3.1. Pasarela

Cuando se implemente Wompi:

- Se genera link.
- Paciente paga.
- Wompi envía webhook.
- Backend valida.
- Pago pasa a `paid`.
- Cita pasa a `confirmed`.

### 3.2. Transferencia manual

Flujo:

```text
Paciente elige transferencia
↓
Sistema muestra instrucciones
↓
Cita queda pending_payment_evidence
↓
Paciente tiene X minutos configurables para enviar evidencia
↓
Si no envía evidencia:
    reserva expira
    slot se libera
↓
Si envía evidencia:
    cita queda pending_manual_payment_review
    slot queda protegido
↓
IA prevalida
↓
Admin revisa contra cuenta bancaria
↓
Admin aprueba o rechaza
```

### 3.3. Pago en sitio

Debe ser configurable.

Si el tenant no acepta pago en sitio, no se ofrece.

Si se acepta:

```text
booking = confirmed_without_payment
payment_status = pay_at_location
```

## 4. Evidencia de transferencia

El sistema debe permitir recibir evidencia:

- Imagen.
- PDF.
- Captura.
- Archivo.

La IA puede extraer:

- Valor.
- Fecha.
- Cuenta destino.
- Referencia.
- Banco.
- Nombre visible.
- Posibles inconsistencias.

Pero debe advertir que la imagen puede ser falsa o manipulada.

## 5. Revisión manual

Pantalla administrativa:

- Paciente.
- Cita.
- Profesional.
- Servicio.
- Fecha.
- Valor esperado.
- Evidencia.
- Resultado IA.
- Botón aprobar.
- Botón rechazar.
- Botón solicitar nueva evidencia.
- Campo notas.
- Confirmación de revisión contra banco.

Debe auditar:

- reviewed_by.
- reviewed_at.
- decision.
- notes.
- confirmed_against_bank.

## 6. Revisión vencida

Cuando el paciente envió evidencia, el horario queda protegido.

Si la revisión vence:

- No liberar automáticamente.
- Marcar `review_overdue`.
- Alertar al administrador.
- Escalar según configuración.

Esto evita castigar al paciente por falta de gestión administrativa.

## 7. No evidencia

Si el paciente no envía evidencia dentro del plazo:

- Expira reserva.
- Libera slot.
- Notifica al paciente.

## 8. Políticas por tenant

Cada tenant puede configurar:

- allow_gateway_payment.
- allow_manual_transfer.
- allow_pay_at_location.
- require_payment_before_confirmation.
- payment_evidence_due_minutes.
- manual_review_due_policy.
- manual_review_due_time.
- auto_expire_if_no_evidence.
- auto_expire_if_review_overdue.
- refund_policy_days.

Valores recomendados:

```text
auto_expire_if_no_evidence = true
auto_expire_if_review_overdue = false
require_manual_review_for_transfers = true
```

## 9. Reembolsos

Si un paciente cancela y ya pagó, el sistema debe manejar reembolso según política del tenant.

El mensaje de cancelación debe informar:

- Que el cupo será liberado.
- Que una nueva reserva depende de disponibilidad.
- Que el reembolso se gestiona en X días configurables.



---

# ADMIN_CONSOLE.md  
# Consola Administrativa de TotalChat

## 1. Propósito

La consola administrativa es necesaria para que los tenants autogestionen su operación.

El bot no puede funcionar correctamente sin datos maestros.

## 2. Stack recomendado

- React.
- TypeScript.
- Vite.
- Tailwind CSS.
- shadcn/ui.
- TanStack Query.
- React Hook Form.
- Zod.

## 3. Autenticación

Recomendación:

- Email/password.
- JWT access token.
- Refresh token.
- Password hash con Argon2 o bcrypt.
- Roles por tenant.

Roles:

```text
owner
admin
staff
readonly
```

## 4. Módulos

### 4.1. Login y tenant selector

Debe permitir iniciar sesión y seleccionar tenant si el usuario pertenece a varios.

### 4.2. Dashboard

Debe mostrar:

- Citas del día.
- Próximas citas.
- Citas pendientes de pago.
- Citas pendientes de revisión manual.
- Citas virtuales sin link.
- Citas sin confirmación de asistencia.
- Alertas de revisión vencida.
- Alertas de link pendiente.
- Servicios activos.
- Profesionales activos.

### 4.3. Organizaciones

CRUD lógico:

- Crear.
- Consultar.
- Editar.
- Deshabilitar.

### 4.4. Sedes

Debe permitir configurar sedes físicas o virtuales.

Campos:

- Nombre.
- Dirección.
- Ciudad.
- Referencia.
- Instrucciones.

### 4.5. Consultorios

Debe permitir crear consultorios asociados a sedes.

### 4.6. Profesionales

Debe permitir:

- Crear profesional.
- Editar profesional.
- Asociar organización.
- Asociar especialidad.
- Deshabilitar.

### 4.7. Especialidades

Debe permitir crear y administrar especialidades.

### 4.8. Servicios del profesional

Debe permitir:

- Crear servicio por profesional.
- Definir duración.
- Definir descripción.
- Definir si requiere pago.
- Definir modalidad.
- Asociar sede/consultorio.
- Deshabilitar servicio.

### 4.9. Precios y planes

Debe permitir:

- Crear tipos de pagador.
- Crear pagadores.
- Crear planes.
- Asignar precios por servicio del profesional y plan.
- Definir vigencia.
- Deshabilitar tarifas.

Debe soportar jerarquía:

```text
payer_type → payer → payer_plan → price
```

### 4.10. Disponibilidad

Debe permitir:

- Crear reglas semanales.
- Definir profesional.
- Definir servicio o todos.
- Definir sede/consultorio.
- Definir modalidad.
- Definir buffers.
- Crear excepciones.

### 4.11. Citas

Debe permitir:

- Ver citas.
- Crear cita manual.
- Cancelar.
- Reprogramar.
- Ver estado.
- Ver pago.
- Ver confirmación de asistencia.

### 4.12. Pacientes

Debe permitir:

- Ver pacientes.
- Crear/editar.
- Completar datos pendientes.
- Asociar planes/coberturas.
- Ver citas administrativas.
- Deshabilitar.

### 4.13. Pagos

Debe permitir:

- Ver pagos.
- Ver comprobantes.
- Ver prevalidación IA.
- Aprobar.
- Rechazar.
- Solicitar nueva evidencia.
- Marcar revisión bancaria.
- Ver revisión vencida.

### 4.14. Citas virtuales

Debe permitir:

- Ver citas virtuales.
- Ver citas sin link.
- Agregar link manual.
- Editar link.
- Marcar link enviado.
- Reenviar link.

### 4.15. Recordatorios

Debe permitir:

- Configurar recordatorios.
- Configurar confirmación de asistencia.
- Ver no confirmados.
- Ver respuestas negativas pendientes de segunda confirmación.

### 4.16. Configuración del bot

Debe permitir:

- Mensajes base.
- Políticas de pago.
- Políticas de cancelación.
- Instrucciones de llegada.
- Instrucciones de citas virtuales.
- Handoff humano.
- Canal Telegram.
- Futuro WhatsApp.

## Módulo Campañas y comunicados

La consola administrativa debe incluir un módulo transversal:

```text
Campañas y comunicados
```

Pantallas mínimas:

```text
Listado de campañas
Crear campaña
Editar borrador
Seleccionar audiencia
Previsualizar audiencia
Previsualizar mensaje
Enviar ahora
Programar envío
Cancelar programada
Detalle de campaña
Entregas
Métricas
```

Campos:

```text
nombre
descripción
tipo de campaña
tipo de mensaje
solución/vertical
audiencia
filtros
canal
mensaje
modo de envío
fecha programada
timezone
```

Antes de enviar, debe mostrarse una confirmación con:

```text
destinatarios estimados
destinatarios elegibles
bloqueados por consentimiento
bloqueados por política de canal
bloqueados por falta de contacto
mensaje final
usuario responsable
```



---

# AI_BOUNDARIES.md  
# Límites de IA en TotalChat

## 1. Principio central

La IA conversa y orquesta, pero no es la fuente de verdad.

## 2. Permitido

La IA puede:

- Entender intención.
- Pedir datos faltantes.
- Resolver ambigüedad.
- Presentar servicios.
- Presentar horarios retornados por herramientas.
- Explicar opciones de pago.
- Guiar paso a paso.
- Redactar mensajes naturales.
- Interpretar respuestas de recordatorios.
- Prevalidar comprobantes de pago.
- Buscar semánticamente servicios y políticas.

## 3. Prohibido

La IA no puede:

- Inventar precios.
- Inventar horarios.
- Confirmar pagos sin herramienta.
- Confirmar citas sin herramienta.
- Inventar links virtuales.
- Diagnosticar.
- Elegir tenant/schema.
- Aprobar transferencias.
- Crear reembolsos no autorizados.
- Modificar reglas del tenant por conversación.
- Saltarse políticas configuradas.

## 4. Herramientas controladas

El agente debe usar herramientas como:

- search_services.
- get_pricing_options.
- get_available_slots.
- create_tentative_booking.
- confirm_booking.
- create_payment_attempt.
- register_payment_evidence.
- get_payment_status.
- cancel_booking.
- reschedule_booking.

## 5. LLMProvider

Debe existir abstracción:

```text
LLMProvider
OpenAIProvider
```

Futuro:

```text
OllamaProvider
```

## 6. OpenAI inicial

OpenAI será el proveedor inicial.

El código debe evitar acoplamiento directo.

## 7. Comprobantes de pago

La IA puede extraer información de comprobantes, pero debe marcar su resultado como prevalidación.

Resultado posible:

```text
Monto coincide
Cuenta parece coincidir
Fecha parece válida
Referencia detectada
Requiere revisión humana
```

Nunca:

```text
Pago confirmado
```

## 8. Emergencias médicas

Si el usuario describe una emergencia, el agente debe recomendar atención inmediata.

No debe diagnosticar.

## 9. pgvector

pgvector apoya búsqueda semántica.

No reemplaza lógica transaccional.

## 10. Auditoría de herramientas

Se deben registrar:

- Intención detectada.
- Herramientas llamadas.
- Resultado resumido.
- Errores.
- Estado conversacional.



---

# SECURITY.md  
# Seguridad, Privacidad y Auditoría

## 1. Principios

TotalChat manejará datos personales administrativos.

No manejará historia clínica en el MVP.

## 2. Secretos

No guardar secretos en repositorio.

Usar variables de entorno:

- OPENAI_API_KEY.
- DATABASE_URL.
- REDIS_URL.
- TELEGRAM_BOT_TOKEN.
- JWT_SECRET.
- WOMPI_KEYS futuras.

## 3. Autenticación admin

Recomendado:

- Email/password.
- Password hash Argon2 o bcrypt.
- JWT access token.
- Refresh token.
- Roles por tenant.

## 4. Autorización

Roles:

```text
owner
admin
staff
readonly
```

Toda acción administrativa debe validar tenant y rol.

## 5. Multi-tenancy

Reglas:

- Resolver tenant antes de acceder a datos.
- Usar schema del tenant.
- No permitir que LLM elija schema.
- No ejecutar herramientas sin contexto tenant.
- Tests de aislamiento obligatorios.

## 6. Webhooks

Telegram y futuros canales deben validar:

- Token/secreto.
- Origen si aplica.
- Payload esperado.
- Tenant channel activo.

## 7. Auditoría

Auditar:

- Login.
- Cambios de contraseña.
- Creación y cambios de usuarios.
- Cambios de roles.
- Cambios de servicios.
- Cambios de precios.
- Cambios de disponibilidad.
- Creación/cancelación/reprogramación de citas.
- Aprobación/rechazo de pagos.
- Actualización de links virtuales.
- Cambios de configuración de pago.

## 8. Datos personales

Minimizar datos.

No pedir datos no necesarios al inicio.

Permitir perfiles incompletos.

## 9. Pagos

Transferencias requieren revisión humana.

La evidencia visual no confirma pago.

## 10. Citas virtuales

Links de reunión deben tratarse como datos sensibles operativos.

Solo usuarios autorizados pueden modificarlos.

## 11. Logs

Evitar loguear secretos.

Evitar loguear información sensible innecesaria.

## 12. Backups

Pendiente definir estrategia exacta.

Debe considerar:

- Backup completo.
- Restauración por tenant.
- Export por schema.



---

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



---

# DECISIONS.md  
# Decisiones del Proyecto TotalChat

## Decisiones cerradas

| Área | Decisión |
|---|---|
| Nombre | TotalChat |
| Repositorio | TotalChat |
| Vertical inicial | Citas médicas / servicios de salud |
| Backend | FastAPI |
| Base de datos | PostgreSQL |
| Multi-tenancy | Schema por tenant |
| Vector search | pgvector desde el inicio |
| Cache/locks | Redis recomendado |
| IA | LangGraph + LangChain |
| LLM inicial | OpenAI |
| LLM futuro | Ollama/laboratorio o proveedores alternativos mediante LLMProvider |
| Canal inicial | Telegram directo |
| Canal futuro | WhatsApp |
| Pagos iniciales | Simulados y transferencia manual |
| Pasarela futura | Wompi |
| Admin web | React/Vite recomendado |
| Auth admin | JWT email/password recomendado |
| Infra | Linux + Docker Compose + Nginx + Let's Encrypt |
| n8n | Complementario, no core |

## Decisiones de dominio

1. La especialidad no define precio.
2. Cada profesional define sus servicios.
3. El precio se define por servicio del profesional y plan comercial.
4. La jerarquía comercial es `payer_type → payer → payer_plan`.
5. El paciente puede tener planes/coberturas, pero el servicio debe tener tarifa para ese plan.
6. La cita guarda snapshot de servicio, precio y plan.
7. El paciente no necesita existir previamente para reservar.
8. El bot puede crear paciente mínimo/incompleto.
9. Transferencias requieren revisión manual.
10. Evidencia enviada protege el slot.
11. Revisión vencida alerta, no libera automáticamente.
12. Recordatorio puede pedir confirmación de asistencia.
13. Respuesta negativa requiere segunda confirmación.
14. No respuesta se maneja según política del tenant.

## Decisiones abiertas

1. Dominio/subdominio inicial.
2. Modelo OpenAI específico.
3. Modelo embeddings específico.
4. Duración default de hold de pago.
5. Tiempo default para evidencia.
6. Hora default de revisión manual.
7. Política default no respuesta.
8. Diseño visual exacto.
9. Estrategia de backups.
10. CI/CD final.

## Decisión — Capa genérica de proveedores de agenda y reuniones

TotalChat mantendrá un motor interno de agenda, pero debe soportar proveedores externos de agenda/calendario y reuniones virtuales por tenant.

La integración no se diseñará como un conector rígido a Docplanner. Docplanner será una implementación de una capa genérica `SchedulingProvider`.

También deben poder existir:

- GoogleCalendarSchedulingProvider.
- MicrosoftCalendarSchedulingProvider.
- OtherSchedulingProvider.

Para reuniones virtuales se usará una capa separada:

- ManualMeetingProvider.
- GoogleMeetProvider.
- MicrosoftTeamsMeetingProvider.
- ZoomMeetingProvider futuro.

Rationale:

- Muchos médicos ya usan Docplanner/Doctoralia como agenda.
- Otros usan Google Calendar o Microsoft 365.
- Ignorar esas agendas puede generar doble reserva.
- Acoplar TotalChat a Docplanner reduciría el alcance del producto.
- TotalChat debe conservar conversación, pagos, precios jerárquicos, revisión manual, recordatorios y consola administrativa.

Decisión:

- Implementar InternalSchedulingProvider como default.
- Implementar ManualMeetingProvider como MVP.
- Diseñar contratos para proveedores externos desde temprano.
- Implementar Docplanner, Google Calendar y Microsoft en fases futuras.


## Decisión — Capa de precisión ejecutable para Codex

TotalChat mantendrá una capa de documentación adicional para hacer más segura la implementación con Codex:

- Contratos API.
- Máquinas de estado.
- Reglas de proveedores de agenda y reuniones.
- Fixtures de prueba.
- Checklist de PR.

Rationale:

La documentación rectora define alcance y arquitectura, pero Codex implementa mejor cuando cada fase tiene contratos, transiciones, datos de prueba y criterios de revisión explícitos.

Decisión:

Antes de iniciar implementación funcional, se deben agregar y mantener:

```text
docs/API_CONTRACTS.md
docs/STATE_MACHINES.md
docs/SCHEDULING_PROVIDER_RULES.md
docs/TEST_FIXTURES.md
docs/PR_REVIEW_CHECKLIST.md
```

## Decisión — TotalChat como plataforma y verticales oficiales

TotalChat será la marca paraguas y plataforma técnica.

Verticales oficiales:

```text
MediChat   = médicos y profesionales de salud
RestoChat  = restaurantes y bares
HotelChat  = hoteles
StayChat   = Airbnb y otros alojamientos
StoreChat  = tiendas y comercio minorista
```

El primer vertical implementado será MediChat.

Rationale:

El nombre TotalChat es amplio y sirve mejor como marca/familia de soluciones. Los clientes entenderán mejor soluciones especializadas por vertical.

Decisión:

- Mantener repositorio inicial `TotalChat`.
- Organizar internamente con `apps/`, `packages/` y `solutions/`.
- Implementar primero `solutions/medichat/`.
- Documentar RestoChat, HotelChat, StayChat y StoreChat como verticales futuros.

## Decisión — Monorepo modular preparado para separación futura

TotalChat iniciará en monorepo modular.

Rationale:

- Un solo desarrollador al inicio.
- Core todavía en definición.
- MediChat será el primer vertical.
- Separar repos prematuramente aumentaría complejidad.
- Codex y SDD funcionan mejor inicialmente con contexto unificado.

Decisión:

Usar estructura:

```text
apps/
packages/
solutions/
docs/
specs/
infra/
scripts/
tests/
```

Separar repos en el futuro solo cuando existan clientes, equipos, releases o roadmaps independientes por vertical.

## Decisión — Campañas y comunicados como capacidad transversal

TotalChat incluirá un módulo transversal de campañas, comunicados y mensajería masiva.

Rationale:

Todos los verticales necesitan enviar mensajes masivos o segmentados: avisos operativos, promociones, cambios de horario, cierres temporales, apertura de agenda, recordatorios generales o información relevante.

Decisión:

- El módulo vivirá como capacidad de plataforma/core.
- La primera implementación será utilizada por MediChat.
- Los resolvers de audiencia serán específicos por vertical.
- Los canales serán provistos por `ChannelProvider`.
- Se debe respetar consentimiento.
- Se deben registrar entregas individuales.
- n8n puede complementar, pero TotalChat será fuente de verdad.



---

# SDD_SPECKIT_GUIDE.md  
# Guía para SDD y Spec Kit en TotalChat

## 1. Enfoque

TotalChat se desarrollará bajo un enfoque SDD.

Flujo:

```text
Spec → Plan → Tasks → Implement
```

La especificación gobierna la implementación.

## 2. Artefactos

Cada feature importante debe tener carpeta en `specs/`.

Estructura:

```text
specs/NNN-feature-name/
├── spec.md
├── plan.md
├── tasks.md
├── data-model.md
├── contracts.md
└── quickstart.md
```

## 3. Specs iniciales

1. 001-project-foundation
2. 002-multitenancy
3. 003-booking-domain
4. 004-admin-console
5. 005-langgraph-agent
6. 006-telegram-channel
7. 007-payments-manual-review
8. 008-reminders-confirmation

## 4. Regla de implementación

Codex no debe implementar código fuera del scope de la spec activa.

Si una tarea requiere desviación, debe documentarse y solicitar aprobación.

## 5. Definition of Ready

Una spec está lista si tiene:

- Objetivo.
- Historias de usuario.
- Requisitos funcionales.
- Requisitos no funcionales.
- Fuera de alcance.
- Criterios de aceptación.
- Riesgos.
- Dependencias.

## 6. Definition of Done

Una implementación está lista si:

- Cumple spec.
- Tiene pruebas.
- No viola constitución.
- No introduce alcance no autorizado.
- Documenta decisiones nuevas.
- Pasa lint/tests.
- Tiene migraciones si aplica.
- Tiene quickstart si aplica.

## 7. Prompt inicial para Spec Kit

```text
Crea la especificación 001 para la fundación de TotalChat.

TotalChat es una plataforma conversacional multi-tenant de reservas, iniciando por citas médicas, con FastAPI, PostgreSQL, schema por tenant, pgvector, Redis, LangGraph, OpenAI, Telegram, consola administrativa, pagos simulados, transferencias con revisión manual, recordatorios y n8n complementario.

La Spec 001 debe limitarse a fundación técnica: estructura repo, FastAPI, frontend base, Docker Compose, PostgreSQL, pgvector, Redis, healthcheck, configuración, logging y documentación base.

No implementar todavía dominio de citas, Telegram, pagos ni agente completo.
```

## 8. Specs adicionales para integraciones externas

Las integraciones externas de agenda y reuniones deben manejarse mediante specs separadas:

```text
011-external-scheduling-provider
012-docplanner-adapter
013-google-calendar-adapter
014-microsoft-calendar-teams-adapter
```

Regla:

- La Spec 011 diseña la abstracción genérica.
- Las Specs 012, 013 y 014 implementan adaptadores concretos.
- Ningún adaptador concreto debe modificar la constitución ni acoplar el core a un proveedor.


## Capa de precisión para Codex

Además de specs, planes y tareas, TotalChat debe mantener documentos ejecutables que reduzcan ambigüedad:

- `docs/API_CONTRACTS.md`
- `docs/STATE_MACHINES.md`
- `docs/SCHEDULING_PROVIDER_RULES.md`
- `docs/TEST_FIXTURES.md`
- `docs/PR_REVIEW_CHECKLIST.md`

Antes de pedir implementación a Codex, la spec activa debe revisar estos documentos y declarar cuáles aplican.

Regla:

```text
Codex no debe inferir libremente contratos, rutas, transiciones de estado ni fixtures cuando estos documentos ya los definen.
```

## Flujo recomendado de implementación por PR

```text
1. Seleccionar spec activa.
2. Confirmar que la spec no viola CONSTITUTION.md.
3. Revisar API_CONTRACTS.md si aplica.
4. Revisar STATE_MACHINES.md si aplica.
5. Revisar SCHEDULING_PROVIDER_RULES.md si toca agenda.
6. Revisar TEST_FIXTURES.md para pruebas.
7. Implementar tareas de tasks.md.
8. Ejecutar pruebas.
9. Revisar PR con PR_REVIEW_CHECKLIST.md.
```



---

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



---

# Specs



## 000-implementation-precision



### spec.md

# Spec 000 — Implementation Precision Layer

## Objetivo

Agregar la capa de precisión necesaria para que Codex implemente TotalChat con contratos, transiciones, fixtures y checklist de revisión.

## Alcance

Incluye:

- API_CONTRACTS.md
- STATE_MACHINES.md
- SCHEDULING_PROVIDER_RULES.md
- TEST_FIXTURES.md
- PR_REVIEW_CHECKLIST.md

No implementa código funcional.

## Criterios de aceptación

1. Los documentos existen.
2. README referencia los documentos.
3. SDD_SPECKIT_GUIDE explica cómo usarlos.
4. Specs iniciales 001, 002 y 003 referencian contratos concretos.
5. Roadmap incluye Fase 0B.



### plan.md

# Plan 000 — Implementation Precision Layer

## Estrategia

Crear documentos Markdown de precisión y actualizar docs/specs existentes.

## Validación

- Verificar existencia de documentos.
- Verificar links/referencias en README.
- Verificar specs 001-003 reforzadas.



### tasks.md

# Tasks 000 — Implementation Precision Layer

- [x] Crear docs/API_CONTRACTS.md.
- [x] Crear docs/STATE_MACHINES.md.
- [x] Crear docs/SCHEDULING_PROVIDER_RULES.md.
- [x] Crear docs/TEST_FIXTURES.md.
- [x] Crear docs/PR_REVIEW_CHECKLIST.md.
- [x] Actualizar README.md.
- [x] Actualizar docs/SDD_SPECKIT_GUIDE.md.
- [x] Actualizar docs/ROADMAP.md.
- [x] Actualizar docs/DECISIONS.md.
- [x] Actualizar docs/MVP_001_SPEC.md.
- [x] Reforzar specs/001 contracts/quickstart.
- [x] Reforzar specs/002 contracts/data-model/quickstart.
- [x] Reforzar specs/003 contracts/data-model/quickstart/tasks.



### contracts.md

# Contracts — Spec 000

No aplica API runtime. Esta spec produce documentación.



### data-model.md

# Data Model — Spec 000

No modifica modelo runtime. Agrega reglas documentales.



### quickstart.md

# Quickstart — Spec 000

Leer README y los cinco documentos nuevos en `docs/`.



## 000b-brand-repository-strategy



### spec.md

# Spec 000B — Brand, Vertical Naming and Repository Strategy

## Objetivo

Formalizar TotalChat como plataforma paraguas, definir nombres oficiales por vertical y establecer política de repositorio monorepo modular.

## Alcance

Incluye:

- TotalChat como marca/plataforma paraguas.
- MediChat como primer vertical.
- RestoChat, HotelChat, StayChat y StoreChat como verticales futuros.
- Política de monorepo.
- Estructura apps/packages/solutions.
- Reglas de separación entre core y verticales.
- Reglas para separación futura de repos.

No incluye:

- Implementación de nuevos verticales.
- Cambio funcional del MVP.
- Creación de repos separados.
- Desarrollo de RestoChat, HotelChat, StayChat o StoreChat.

## Requisitos

1. Documentar nombres oficiales.
2. Documentar estructura recomendada.
3. Documentar política de imports.
4. Documentar cuándo separar repos.
5. Actualizar constitución.
6. Actualizar arquitectura.
7. Actualizar decisiones.
8. Actualizar roadmap.
9. Actualizar checklist de PR.

## Criterios de aceptación

1. Existe `docs/BRAND_AND_PRODUCT_STRATEGY.md`.
2. Existe `docs/REPOSITORY_STRATEGY.md`.
3. Existe `docs/SOLUTION_ARCHITECTURE.md`.
4. README menciona verticales oficiales.
5. Constitución define TotalChat como plataforma paraguas.
6. PR checklist valida separación core/vertical.



### plan.md

# Plan 000B — Brand, Vertical Naming and Repository Strategy

## Estrategia

Actualizar documentación sin implementar código.

## Decisiones

- TotalChat = plataforma paraguas.
- MediChat = primer vertical.
- RestoChat = restaurantes y bares.
- HotelChat = hoteles.
- StayChat = Airbnb y otros alojamientos.
- StoreChat = tiendas y comercio minorista.
- Monorepo inicial.
- Separación futura solo cuando haya madurez.

## Archivos

- docs/BRAND_AND_PRODUCT_STRATEGY.md
- docs/REPOSITORY_STRATEGY.md
- docs/SOLUTION_ARCHITECTURE.md
- README.md
- docs/CONSTITUTION.md
- docs/ARCHITECTURE.md
- docs/DATA_MODEL.md
- docs/ROADMAP.md
- docs/DECISIONS.md
- docs/MVP_001_SPEC.md
- docs/PR_REVIEW_CHECKLIST.md



### tasks.md

# Tasks 000B — Brand, Vertical Naming and Repository Strategy

- [x] Crear docs/BRAND_AND_PRODUCT_STRATEGY.md.
- [x] Crear docs/REPOSITORY_STRATEGY.md.
- [x] Crear docs/SOLUTION_ARCHITECTURE.md.
- [x] Actualizar README.md.
- [x] Actualizar docs/CONSTITUTION.md.
- [x] Actualizar docs/ARCHITECTURE.md.
- [x] Actualizar docs/DATA_MODEL.md.
- [x] Actualizar docs/ROADMAP.md.
- [x] Actualizar docs/DECISIONS.md.
- [x] Actualizar docs/MVP_001_SPEC.md.
- [x] Actualizar docs/PR_REVIEW_CHECKLIST.md.



### contracts.md

# Contracts — Spec 000B

No aplica API runtime. Esta spec actualiza estrategia documental.



### data-model.md

# Data Model — Spec 000B

## public.solutions

```text
id
code
name
description
status
created_at
updated_at
```

Registros iniciales:

```text
medichat
restochat
hotelchat
staychat
storechat
```

## public.tenant_solutions

```text
id
tenant_id
solution_id
status
settings
created_at
updated_at
```

Para MVP se usará `medichat`.



### quickstart.md

# Quickstart — Spec 000B

Leer:

- docs/BRAND_AND_PRODUCT_STRATEGY.md
- docs/REPOSITORY_STRATEGY.md
- docs/SOLUTION_ARCHITECTURE.md

Validar que:

- TotalChat está definido como plataforma.
- MediChat está definido como primer vertical.
- RestoChat, HotelChat, StayChat y StoreChat están documentados como futuros.
- La estructura monorepo está definida.



## 001-project-foundation



### spec.md

# Spec 001 — Project Foundation

## Objetivo

Crear la base técnica del proyecto TotalChat.

## Alcance

Incluye:

- Estructura de repo.
- Backend FastAPI.
- Frontend admin base.
- Docker Compose.
- PostgreSQL.
- pgvector.
- Redis.
- Healthchecks.
- Configuración.
- Logging.
- Documentación base.

No incluye:

- Dominio de reservas.
- Telegram.
- Pagos.
- LangGraph completo.

## Requisitos funcionales

1. El backend debe iniciar.
2. Debe existir `GET /health`.
3. Docker Compose debe levantar backend, postgres y redis.
4. PostgreSQL debe tener pgvector habilitado.
5. El frontend debe iniciar como app base.
6. Debe existir `.env.example`.
7. Deben existir docs iniciales.

## Requisitos no funcionales

- Configuración por variables de entorno.
- Logs básicos.
- Pruebas mínimas.
- Preparado para Linux/Docker.

## Criterios de aceptación

- `docker compose up` levanta servicios.
- `/health` responde OK.
- Redis responde.
- PostgreSQL responde.
- pgvector está disponible.
- Tests base pasan.



### plan.md

# Plan 001 — Project Foundation

## Stack

- FastAPI.
- SQLAlchemy.
- Alembic.
- PostgreSQL + pgvector.
- Redis.
- React + Vite.
- Docker Compose.

## Pasos

1. Crear estructura repo.
2. Crear backend FastAPI.
3. Crear frontend Vite.
4. Crear Dockerfile backend.
5. Crear Dockerfile frontend si aplica.
6. Crear docker-compose.
7. Configurar PostgreSQL.
8. Habilitar pgvector.
9. Configurar Redis.
10. Crear healthcheck.
11. Crear tests.
12. Actualizar docs.

## Riesgos

- Complejidad inicial excesiva.
- Configuración de pgvector.
- Incompatibilidades Docker.

## Validación

- Levantar stack.
- Ejecutar tests.
- Verificar health.



### tasks.md

# Tasks 001 — Project Foundation

- [ ] Crear estructura de carpetas.
- [ ] Crear backend FastAPI.
- [ ] Crear endpoint `/health`.
- [ ] Crear configuración con Pydantic Settings.
- [ ] Configurar logging.
- [ ] Crear frontend Vite React.
- [ ] Configurar Tailwind.
- [ ] Crear Docker Compose.
- [ ] Agregar PostgreSQL.
- [ ] Agregar pgvector.
- [ ] Agregar Redis.
- [ ] Crear `.env.example`.
- [ ] Crear tests health.
- [ ] Documentar quickstart.



### contracts.md

# Contracts — Spec 001 Project Foundation

## Endpoints

### GET /health

Debe responder si el backend está vivo.

Response:

```json
{
  "data": {
    "status": "ok",
    "service": "totalchat-api",
    "version": "0.1.0"
  }
}
```

### GET /ready

Debe validar dependencias mínimas.

Response:

```json
{
  "data": {
    "status": "ready",
    "database": "ok",
    "redis": "ok"
  }
}
```

## Reglas

- No implementar dominio de negocio en esta spec.
- No implementar Telegram en esta spec.
- No implementar pagos en esta spec.
- No implementar LangGraph completo en esta spec.
- Sí dejar estructura preparada para módulos futuros.

## Validación

- `docker compose up` levanta servicios.
- `/health` responde 200.
- `/ready` responde 200 cuando PostgreSQL y Redis están disponibles.
- Tests base pasan.



### data-model.md

# Data Model — 001-project-foundation

Ver `docs/DATA_MODEL.md`. Detalles específicos se completarán durante esta spec.



### quickstart.md

# Quickstart — Spec 001 Project Foundation

## Objetivo

Validar que la fundación técnica de TotalChat levanta correctamente.

## Pasos esperados

```bash
cp .env.example .env
docker compose up --build
```

Validar backend:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

Ejecutar pruebas:

```bash
cd backend
pytest
```

Validar frontend:

```bash
cd frontend
npm install
npm run dev
```

## Resultado esperado

- Backend responde health.
- PostgreSQL está disponible.
- Redis está disponible.
- Frontend carga pantalla base.
- No existen funcionalidades de negocio todavía.



## 002-multitenancy



### spec.md

# Spec 002 — Multi-Tenant Schema Architecture

## Objetivo

Implementar multi-tenancy por schema PostgreSQL.

## Alcance

- Schema public.
- Tenants.
- Tenant channels.
- Users.
- User tenants.
- Provisioning de schema.
- Tenant resolver.
- Tests de aislamiento.

## Requisitos

1. Crear tenant en `public.tenants`.
2. Crear schema asociado.
3. Aplicar migraciones base al schema.
4. Resolver tenant por canal.
5. Ejecutar operaciones dentro del schema correcto.
6. Prohibir herramientas sin contexto tenant.

## Criterios de aceptación

- Dos tenants pueden tener datos con mismos IDs lógicos sin mezclarse.
- Una consulta de tenant A no ve datos de tenant B.
- El resolver funciona por tenant_channel.



### plan.md

# Plan 002 — Multi-Tenancy

## Diseño

Usar schema `public` para control y un schema por tenant.

## Componentes

- Tenant model.
- TenantChannel model.
- TenantProvisioningService.
- TenantResolver.
- TenantContext.
- Migration runner por schema.

## Validación

- Tests con tenant_a y tenant_b.
- Verificar aislamiento.



### tasks.md

# Tasks 002 — Multi-Tenancy

- [ ] Crear migraciones public.
- [ ] Crear modelo Tenant.
- [ ] Crear modelo TenantChannel.
- [ ] Crear modelo User.
- [ ] Crear modelo UserTenant.
- [ ] Crear TenantProvisioningService.
- [ ] Crear función de creación de schema.
- [ ] Crear migraciones tenant base.
- [ ] Crear TenantResolver.
- [ ] Crear TenantContext.
- [ ] Crear tests de aislamiento.



### contracts.md

# Contracts — Spec 002 Multi-Tenancy

## Endpoints

### POST /api/platform/tenants

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

### GET /api/platform/tenants

Lista tenants.

### POST /api/platform/tenants/{tenant_id}/channels

Request Telegram:

```json
{
  "channel_type": "telegram",
  "external_identifier": "totalchat_demo_bot",
  "settings": {
    "webhook_enabled": true
  }
}
```

## Reglas

- El backend genera `schema_name`.
- No exponer `schema_name` al frontend de forma innecesaria.
- El LLM no participa en resolver tenants.
- Toda operación admin futura debe tener contexto tenant validado.
- Deben existir tests de aislamiento.

## Errores

- `TENANT_NOT_FOUND`
- `VALIDATION_ERROR`
- `CONFLICT`
- `AUTHORIZATION_FAILED`



### data-model.md

# Data Model — Spec 002 Multi-Tenancy

## public.tenants

```text
id
name
slug
schema_name
status
plan_id nullable
created_at
updated_at
```

## public.tenant_channels

```text
id
tenant_id
channel_type
external_identifier
webhook_secret_hash nullable
settings
is_active
created_at
updated_at
```

## public.users

```text
id
email
password_hash
full_name
status
created_at
updated_at
```

## public.user_tenants

```text
user_id
tenant_id
role
status
created_at
updated_at
```

## Reglas

- `slug` único.
- `schema_name` único.
- `schema_name` derivado y sanitizado.
- No usar schema sin registro tenant activo.



### quickstart.md

# Quickstart — Spec 002 Multi-Tenancy

## Crear tenant demo

```bash
curl -X POST http://localhost:8000/api/platform/tenants \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Consultorio Psicóloga Ana",
    "slug": "psicologa-ana",
    "owner_email": "ana@example.com",
    "owner_full_name": "Ana Gómez",
    "provision_schema": true
  }'
```

## Validaciones

1. Existe registro en `public.tenants`.
2. Existe schema del tenant.
3. Las migraciones base se aplicaron al schema.
4. Crear dos tenants no mezcla datos.
5. Usuario solo accede a tenants asignados.



## 003-booking-domain



### spec.md

# Spec 003 — Booking Domain Core

## Objetivo

Implementar el dominio base de reservas médicas.

## Alcance

- Organizaciones.
- Sedes.
- Consultorios.
- Profesionales.
- Especialidades.
- Servicios del profesional.
- Modalidades.
- Jerarquía comercial.
- Tarifas.
- Pacientes mínimos.
- Disponibilidad.
- Citas.

## Reglas clave

- Especialidad no define precio.
- Servicio pertenece al profesional.
- Precio depende de servicio + payer_plan.
- Cita guarda snapshot.
- Paciente previo no es requisito.

## Criterios

- Crear servicio del profesional.
- Crear plan comercial.
- Crear precio por servicio/plan.
- Crear paciente mínimo.
- Crear cita con snapshot.



### plan.md

# Plan 003 — Booking Domain

## Entidades

- organizations
- locations
- rooms
- practitioners
- specialties
- practitioner_services
- service_modalities
- payer_types
- payers
- payer_plans
- practitioner_service_prices
- patients
- availability_rules
- bookings

## Servicios

- PractitionerService
- PricingService
- AvailabilityService
- BookingService
- PatientService

## Validación

Pruebas unitarias por dominio.



### tasks.md

# Tasks 003 — Booking Domain

- [ ] Crear organizations.
- [ ] Crear locations.
- [ ] Crear rooms.
- [ ] Crear practitioners.
- [ ] Crear specialties.
- [ ] Crear practitioner_specialties.
- [ ] Crear practitioner_services.
- [ ] Crear service_modalities.
- [ ] Crear payer_types.
- [ ] Crear payers.
- [ ] Crear payer_plans.
- [ ] Crear practitioner_service_prices.
- [ ] Crear patients.
- [ ] Crear patient_contacts.
- [ ] Crear availability_rules.
- [ ] Crear availability_exceptions.
- [ ] Crear bookings.
- [ ] Crear snapshots.
- [ ] Crear tests.


## Tareas adicionales de precisión

- [ ] Validar endpoints contra `docs/API_CONTRACTS.md`.
- [ ] Implementar transiciones según `docs/STATE_MACHINES.md`.
- [ ] Implementar BookingService usando `SchedulingProvider`.
- [ ] Crear fixtures de prueba basados en `docs/TEST_FIXTURES.md`.
- [ ] Validar PR con `docs/PR_REVIEW_CHECKLIST.md`.



### contracts.md

# Contracts — Spec 003 Booking Domain Core

Este documento usa `docs/API_CONTRACTS.md` como fuente principal.

## Endpoints mínimos de dominio

### Organizaciones

- POST `/api/admin/organizations`
- GET `/api/admin/organizations`
- GET `/api/admin/organizations/{organization_id}`
- PATCH `/api/admin/organizations/{organization_id}`
- POST `/api/admin/organizations/{organization_id}/disable`

### Sedes y consultorios

- POST `/api/admin/locations`
- GET `/api/admin/locations`
- POST `/api/admin/rooms`
- GET `/api/admin/rooms`

### Profesionales

- POST `/api/admin/practitioners`
- GET `/api/admin/practitioners`
- PATCH `/api/admin/practitioners/{practitioner_id}`

### Especialidades

- POST `/api/admin/specialties`
- GET `/api/admin/specialties`

### Servicios

- POST `/api/admin/practitioner-services`
- GET `/api/admin/practitioner-services`
- POST `/api/admin/practitioner-services/{service_id}/modalities`

### Precios

- POST `/api/admin/payer-types`
- POST `/api/admin/payers`
- POST `/api/admin/payer-plans`
- POST `/api/admin/practitioner-service-prices`
- GET `/api/admin/practitioner-services/{service_id}/prices`

### Pacientes

- POST `/api/admin/patients`
- POST `/api/admin/patients/{patient_id}/payer-profiles`

### Disponibilidad

- POST `/api/admin/availability-rules`
- POST `/api/admin/availability-exceptions`
- GET `/api/admin/availability/slots`

### Citas

- POST `/api/admin/bookings`
- POST `/api/admin/bookings/{booking_id}/confirm`
- POST `/api/admin/bookings/{booking_id}/cancel`
- POST `/api/admin/bookings/{booking_id}/reschedule`

## Reglas

- Seguir `docs/API_CONTRACTS.md`.
- Estados deben seguir `docs/STATE_MACHINES.md`.
- Disponibilidad debe pasar por `SchedulingProvider`.
- Citas deben guardar snapshot.
- Paciente mínimo debe ser válido.
- Precio desconocido no debe inventarse.



### data-model.md

# Data Model — Spec 003 Booking Domain Core

Este spec implementa el subconjunto de dominio descrito en `docs/DATA_MODEL.md`.

# DATA_MODEL.md  
# Modelo de Datos Conceptual de TotalChat

## 1. Principio general

TotalChat usará PostgreSQL con:

- Schema `public` para control SaaS.
- Un schema por tenant para datos operativos.
- pgvector para búsqueda semántica.

El modelo prioriza:

- Multi-tenancy.
- Flexibilidad comercial.
- Snapshot histórico.
- Auditoría.
- Seguridad.
- Evolución futura.

---

# 2. Schema public

## 2.1. tenants

Representa cada cliente de TotalChat.

Campos conceptuales:

```text
id
name
slug
schema_name
status
plan_id
created_at
updated_at
```

## 2.2. tenant_channels

Canales configurados por tenant.

```text
id
tenant_id
channel_type
external_identifier
webhook_secret_hash
settings
is_active
created_at
updated_at
```

`channel_type`:

```text
telegram
whatsapp
web
```

## 2.3. tenant_domains

Dominios o subdominios del tenant.

```text
id
tenant_id
domain
is_primary
status
```

## 2.4. users

Usuarios administrativos.

```text
id
email
password_hash
full_name
status
created_at
updated_at
```

## 2.5. user_tenants

Relación usuario-tenant.

```text
user_id
tenant_id
role
status
```

Roles:

```text
owner
admin
staff
readonly
```

## 2.6. plans / subscriptions

Para futuro manejo SaaS.

```text
plans
subscriptions
```

---

# 3. Schema tenant

Cada tenant tiene su propio schema.

Ejemplo:

```text
tenant_dra_ana
tenant_clinica_vida
```

---

# 4. Organizaciones y ubicaciones

## 4.1. organizations

```text
id
name
organization_type
legal_name
tax_id
email
phone
status
created_at
updated_at
```

`organization_type`:

```text
independent_practitioner
clinic
health_center
office
other
```

## 4.2. locations

```text
id
organization_id
name
address
city
neighborhood
reference
is_virtual
status
created_at
updated_at
```

## 4.3. rooms

```text
id
location_id
name
room_type
capacity
status
created_at
updated_at
```

---

# 5. Profesionales y especialidades

## 5.1. practitioners

```text
id
full_name
professional_type
professional_license
email
phone
status
created_at
updated_at
```

## 5.2. organization_practitioners

```text
organization_id
practitioner_id
role
status
```

## 5.3. specialties

```text
id
name
description
status
```

## 5.4. practitioner_specialties

```text
practitioner_id
specialty_id
status
```

---

# 6. Servicios

## 6.1. service_catalog

Catálogo opcional de referencia, sin precio obligatorio.

```text
id
name
description
specialty_id
status
```

## 6.2. practitioner_services

Entidad central de lo reservable.

```text
id
organization_id
practitioner_id
service_catalog_id nullable
name
description
duration_minutes
requires_payment
status
created_at
updated_at
```

No debe tener precio único rígido.

## 6.3. service_modalities

```text
id
practitioner_service_id
modality
location_id nullable
room_id nullable
status
```

`modality`:

```text
in_person
virtual
both
```

---

# 7. Precios y condiciones comerciales

## 7.1. Modelo jerárquico

El precio se basa en:

```text
payer_type → payer → payer_plan → practitioner_service_price
```

Ejemplo:

```text
Particular
  → Particular
    → Tarifa particular

Medicina prepagada
  → Sura
    → Póliza básica
    → Póliza mejorada

Medicina prepagada
  → Colsanitas
    → Plan inicial
    → Plan avanzado

Póliza de salud
  → Aseguradora ABC
    → Plan pequeño
```

## 7.2. payer_types

```text
id
code
name
description
status
```

Ejemplos:

```text
particular
eps
medicina_prepagada
poliza_salud
convenio_empresarial
otro
```

## 7.3. payers

```text
id
payer_type_id
name
description
status
```

Ejemplos:

```text
Particular
Sura
Colsanitas
Aseguradora ABC
Nueva EPS
Empresa XYZ
```

## 7.4. payer_plans

```text
id
payer_id
name
description
status
```

Ejemplos:

```text
Tarifa particular
Póliza básica
Póliza mejorada
Plan inicial
Plan avanzado
Plan pequeño
```

## 7.5. practitioner_service_prices

Precio específico por servicio del profesional y plan.

```text
id
practitioner_service_id
payer_plan_id
price
currency
valid_from
valid_to
status
```

## 7.6. patient_payer_profiles

Planes o coberturas declaradas/asociadas al paciente.

```text
id
patient_id
payer_plan_id
member_id nullable
status
validation_status
valid_from
valid_to
created_at
updated_at
```

`validation_status`:

```text
declared
pending_validation
validated
rejected
expired
```

---

# 8. Pacientes

## 8.1. patients

```text
id
full_name
phone nullable
email nullable
document_type nullable
document_number nullable
profile_status
created_from_channel
created_at
updated_at
```

`profile_status`:

```text
minimal
incomplete
complete
verified
inactive
```

## 8.2. patient_contacts

```text
id
patient_id
channel_type
value
external_id nullable
is_primary
is_verified
status
```

## 8.3. required_patient_fields

Configuración por tenant de datos obligatorios por etapa.

```text
id
field_code
required_stage
is_required
status
```

`required_stage`:

```text
before_booking
before_payment
before_confirmation
before_appointment
before_invoice
at_reception
```

---

# 9. Disponibilidad

## 9.1. availability_rules

```text
id
organization_id
practitioner_id
practitioner_service_id nullable
location_id nullable
room_id nullable
modality
weekday
start_time
end_time
valid_from
valid_to
buffer_minutes
status
```

## 9.2. availability_exceptions

```text
id
practitioner_id
location_id nullable
room_id nullable
starts_at
ends_at
exception_type
reason
status
```

`exception_type`:

```text
vacation
sick_leave
administrative_block
special_schedule
holiday
manual_block
```

---

# 10. Citas

## 10.1. bookings

```text
id
organization_id
patient_id
practitioner_id
practitioner_service_id
payer_type_id nullable
payer_id nullable
payer_plan_id nullable
location_id nullable
room_id nullable
modality
starts_at
ends_at
status
payment_status
attendance_confirmation_status
service_name_snapshot
duration_minutes_snapshot
practitioner_name_snapshot
payer_type_name_snapshot nullable
payer_name_snapshot nullable
payer_plan_name_snapshot nullable
price_snapshot
currency_snapshot
total_amount
address_snapshot nullable
room_snapshot nullable
created_channel
pending_patient_data
created_at
updated_at
```

## 10.2. booking_status_history

```text
id
booking_id
previous_status
new_status
changed_by_type
changed_by_id nullable
reason
created_at
```

## 10.3. Estados de cita

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
```

---

# 11. Citas virtuales

## 11.1. booking_virtual_details

```text
id
booking_id
provider
meeting_url
meeting_id
access_code
status
created_mode
created_at
updated_at
```

`provider`:

```text
manual
teams
google_meet
zoom
jitsi
other
```

`status`:

```text
pending
created
sent
cancelled
failed
```

`created_mode`:

```text
manual
automatic
external
```

---

# 12. Pagos

## 12.1. tenant_payment_settings

```text
id
allow_gateway_payment
allow_manual_transfer
allow_pay_at_location
require_payment_before_confirmation
auto_confirm_gateway_payments
require_manual_review_for_transfers
payment_evidence_due_minutes
manual_review_due_policy
manual_review_due_time
manual_review_business_days_only
auto_expire_if_no_evidence
auto_expire_if_review_overdue
refund_policy_days
refund_policy_message
```

## 12.2. payment_attempts

```text
id
booking_id
method
provider
amount_expected
amount_received nullable
currency
status
external_reference nullable
payment_url nullable
expires_at nullable
created_at
updated_at
```

`method`:

```text
gateway
manual_transfer
pay_at_location
simulated
```

`status`:

```text
pending
pending_evidence
evidence_uploaded
pending_manual_review
review_overdue
approved
rejected
paid
failed
expired_no_evidence
expired
pay_at_location
```

## 12.3. payment_evidence

```text
id
payment_attempt_id
file_url
file_type
uploaded_by
uploaded_at
ai_extracted_data
ai_prevalidation_status
ai_prevalidation_notes
```

## 12.4. payment_reviews

```text
id
payment_attempt_id
reviewed_by
reviewed_at
decision
notes
confirmed_against_bank
previous_status
new_status
```

`decision`:

```text
approved
rejected
needs_more_evidence
```

## 12.5. refunds

```text
id
booking_id
payment_attempt_id
amount
currency
status
reason
due_days
processed_at
notes
```

---

# 13. Recordatorios

## 13.1. appointment_confirmation_settings

```text
id
enabled
reminder_hours_before
require_attendance_confirmation
second_confirmation_on_negative_response
no_response_policy
no_response_deadline_hours_before
auto_cancel_on_no_response
refund_policy_days
refund_policy_message
```

`no_response_policy`:

```text
mark_unconfirmed
send_second_reminder
notify_admin
auto_cancel
```

---

# 14. Conversaciones

## 14.1. conversation_sessions

```text
id
channel_type
external_user_id
patient_id nullable
booking_id nullable
status
state
created_at
updated_at
```

## 14.2. messages

```text
id
conversation_session_id
direction
message_type
content
raw_payload
intent nullable
tool_calls nullable
created_at
```

---

# 15. Semántica y pgvector

## 15.1. semantic_documents

```text
id
source_type
source_id
content
metadata
embedding
embedding_provider
embedding_model
embedding_version
status
created_at
updated_at
```

Usos:

- Servicios.
- Especialidades.
- FAQ.
- Políticas.
- Instrucciones.

---

# 16. Eventos

## 16.1. domain_events

```text
id
event_type
aggregate_type
aggregate_id
payload
status
created_at
processed_at nullable
```

Ejemplos:

```text
booking.created
booking.confirmed
payment.evidence_uploaded
payment.review_overdue
reminder.due
attendance.confirmed
attendance.declined
virtual_link.pending
```

# 17. Integraciones externas de agenda, calendario y reuniones

## 17.1. external_systems

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

## 17.2. scheduling_provider_configs

Define el proveedor de agenda activo por tenant, organización o profesional.

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

## 17.3. meeting_provider_configs

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

## 17.4. external_practitioner_mappings

```text
id
practitioner_id
external_system_id
external_practitioner_id
raw_external_payload
status
last_synced_at
```

## 17.5. external_location_mappings

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

## 17.6. external_service_mappings

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

## 17.7. external_booking_mappings

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

## 17.8. external_events

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

## 17.9. external_sync_runs

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



### quickstart.md

# Quickstart — Spec 003 Booking Domain Core

## Objetivo

Crear datos mínimos para reservar una cita interna.

## Secuencia

1. Crear organización.
2. Crear sede.
3. Crear consultorio.
4. Crear profesional.
5. Crear especialidad.
6. Asociar profesional a especialidad.
7. Crear servicio del profesional.
8. Crear modalidad.
9. Crear payer_type Particular.
10. Crear payer Particular.
11. Crear payer_plan Tarifa particular.
12. Crear precio del servicio.
13. Crear disponibilidad.
14. Consultar slots.
15. Crear paciente mínimo.
16. Crear booking.
17. Validar snapshot.

## Resultado esperado

```text
booking.status = tentative or pending_payment
booking.service_name_snapshot is not null
booking.price_snapshot is not null
booking.payer_plan_name_snapshot is not null
patient.profile_status = minimal or incomplete
```

## Fixture recomendado

Usar `docs/TEST_FIXTURES.md`, tenant demo `Consultorio Psicóloga Ana`.



## 004-admin-console



### spec.md

# Spec 004 — Admin Console MVP

## Objetivo

Crear consola administrativa mínima para autogestionar datos del tenant.

## Alcance

- Login.
- Dashboard.
- Organizaciones.
- Sedes.
- Consultorios.
- Profesionales.
- Especialidades.
- Servicios.
- Tarifas.
- Disponibilidad.
- Citas.
- Pacientes.
- Pagos.
- Links virtuales.

## Criterios

- Admin puede crear datos necesarios para que el bot reserve.
- Admin puede revisar pagos.
- Admin puede agregar link virtual.



### plan.md

# Plan 004 — Admin Console

## Stack

React + TypeScript + Vite + Tailwind + shadcn/ui.

## Módulos

- Auth.
- Layout.
- Dashboard.
- CRUDs.
- Forms.
- Tables.
- API client.

## Validación

Pruebas manuales y unitarias básicas.



### tasks.md

# Tasks 004 — Admin Console

- [ ] Crear app frontend.
- [ ] Crear login.
- [ ] Crear layout.
- [ ] Crear dashboard.
- [ ] CRUD organizaciones.
- [ ] CRUD sedes.
- [ ] CRUD consultorios.
- [ ] CRUD profesionales.
- [ ] CRUD especialidades.
- [ ] CRUD servicios.
- [ ] CRUD tarifas.
- [ ] Pantalla disponibilidad.
- [ ] Pantalla citas.
- [ ] Pantalla pagos.
- [ ] Pantalla links virtuales.



### contracts.md

# Contracts — 004-admin-console

Pendiente de definir endpoints/API contracts durante el plan técnico.



### data-model.md

# Data Model — 004-admin-console

Ver `docs/DATA_MODEL.md`. Detalles específicos se completarán durante esta spec.



### quickstart.md

# Quickstart — 004-admin-console

Pendiente de completar durante el plan técnico de esta spec.



## 005-langgraph-agent



### spec.md

# Spec 005 — LangGraph Booking Agent

## Objetivo

Crear agente conversacional para reservas.

## Alcance

- LLMProvider.
- OpenAIProvider.
- EmbeddingsProvider.
- LangGraph.
- Tools.
- Estado conversacional.
- Búsqueda semántica.
- Conversaciones simuladas.

## Reglas

- IA no inventa precios.
- IA no inventa disponibilidad.
- IA no confirma pagos.
- Tools ejecutan dominio.



### plan.md

# Plan 005 — LangGraph Agent

## Componentes

- ai/providers.
- ai/graphs.
- ai/tools.
- ai/prompts.
- conversation state.

## Flujo

receive → classify → collect → search → availability → booking → payment → response.

## Validación

Conversaciones simuladas.



### tasks.md

# Tasks 005 — LangGraph Agent

- [ ] Crear LLMProvider.
- [ ] Crear OpenAIProvider.
- [ ] Crear EmbeddingsProvider.
- [ ] Crear semantic_documents.
- [ ] Crear graph state.
- [ ] Crear booking graph.
- [ ] Crear tools de servicios.
- [ ] Crear tools de precios.
- [ ] Crear tools de disponibilidad.
- [ ] Crear tools de citas.
- [ ] Crear tools de pagos.
- [ ] Crear tests conversacionales.



### contracts.md

# Contracts — 005-langgraph-agent

Pendiente de definir endpoints/API contracts durante el plan técnico.



### data-model.md

# Data Model — 005-langgraph-agent

Ver `docs/DATA_MODEL.md`. Detalles específicos se completarán durante esta spec.



### quickstart.md

# Quickstart — 005-langgraph-agent

Pendiente de completar durante el plan técnico de esta spec.



## 006-telegram-channel



### spec.md

# Spec 006 — Telegram Channel

## Objetivo

Conectar TotalChat a Telegram.

## Alcance

- Webhook.
- Tenant resolver por canal.
- Persistencia de mensajes.
- Envío de respuestas.
- Flujo de reserva básico.

## Criterios

- Mensaje entrante se asocia al tenant.
- Se crea sesión.
- Se invoca agente.
- Se responde al usuario.



### plan.md

# Plan 006 — Telegram

## Componentes

- Telegram webhook.
- Telegram client.
- Channel resolver.
- Message persistence.
- Agent bridge.



### tasks.md

# Tasks 006 — Telegram

- [ ] Crear endpoint webhook.
- [ ] Configurar token.
- [ ] Resolver tenant.
- [ ] Persistir incoming messages.
- [ ] Invocar agente.
- [ ] Enviar respuesta.
- [ ] Probar flujo básico.



### contracts.md

# Contracts — 006-telegram-channel

Pendiente de definir endpoints/API contracts durante el plan técnico.



### data-model.md

# Data Model — 006-telegram-channel

Ver `docs/DATA_MODEL.md`. Detalles específicos se completarán durante esta spec.



### quickstart.md

# Quickstart — 006-telegram-channel

Pendiente de completar durante el plan técnico de esta spec.



## 007-payments-manual-review



### spec.md

# Spec 007 — Payments and Manual Review

## Objetivo

Implementar pagos simulados, transferencia, evidencia y revisión manual.

## Reglas

- Si no hay evidencia en tiempo, liberar reserva.
- Si hay evidencia, proteger reserva.
- Revisión vencida no libera automáticamente.
- IA solo prevalida.
- Admin aprueba/rechaza.

## Criterios

- Evidencia se carga.
- Admin revisa.
- Pago aprobado confirma cita.
- Pago rechazado sigue política.



### plan.md

# Plan 007 — Payments

## Componentes

- Payment settings.
- Payment attempts.
- Evidence.
- Reviews.
- Expiration job.
- Review overdue alerts.
- Admin UI.



### tasks.md

# Tasks 007 — Payments

- [ ] Crear payment_settings.
- [ ] Crear payment_attempts.
- [ ] Crear payment_evidence.
- [ ] Crear payment_reviews.
- [ ] Implementar transferencia.
- [ ] Implementar expiración por no evidencia.
- [ ] Implementar protección por evidencia.
- [ ] Implementar revisión manual.
- [ ] Implementar review_overdue.
- [ ] Crear UI pagos pendientes.
- [ ] Crear tests.



### contracts.md

# Contracts — 007-payments-manual-review

Pendiente de definir endpoints/API contracts durante el plan técnico.



### data-model.md

# Data Model — 007-payments-manual-review

Ver `docs/DATA_MODEL.md`. Detalles específicos se completarán durante esta spec.



### quickstart.md

# Quickstart — 007-payments-manual-review

Pendiente de completar durante el plan técnico de esta spec.



## 008-reminders-confirmation



### spec.md

# Spec 008 — Reminders and Attendance Confirmation

## Objetivo

Implementar recordatorios y confirmación de asistencia.

## Reglas

- Enviar recordatorio por mismo canal.
- Confirmación positiva mantiene cita.
- Respuesta negativa requiere segunda confirmación.
- No respuesta según política tenant.
- Reembolso según política.

## Criterios

- Reminder se genera.
- Usuario confirma.
- Usuario declina y confirma cancelación.
- Slot se libera tras cancelación confirmada.



### plan.md

# Plan 008 — Reminders

## Componentes

- Confirmation settings.
- Reminder scheduler/events.
- Response handler.
- Second confirmation flow.
- n8n webhook optional.



### tasks.md

# Tasks 008 — Reminders

- [ ] Crear appointment_confirmation_settings.
- [ ] Crear eventos reminder_due.
- [ ] Enviar recordatorio.
- [ ] Procesar confirmación positiva.
- [ ] Procesar respuesta negativa.
- [ ] Pedir segunda confirmación.
- [ ] Cancelar tras segunda confirmación.
- [ ] Manejar no respuesta.
- [ ] Emitir eventos n8n.
- [ ] Crear tests.



### contracts.md

# Contracts — 008-reminders-confirmation

Pendiente de definir endpoints/API contracts durante el plan técnico.



### data-model.md

# Data Model — 008-reminders-confirmation

Ver `docs/DATA_MODEL.md`. Detalles específicos se completarán durante esta spec.



### quickstart.md

# Quickstart — 008-reminders-confirmation

Pendiente de completar durante el plan técnico de esta spec.



## 011-external-scheduling-provider



### spec.md

# Spec 011 — External Scheduling Provider Abstraction

## Objetivo

Permitir que TotalChat use proveedores internos o externos de agenda/calendario por tenant sin acoplar el core a un proveedor específico.

## Problema

Algunos profesionales ya usan agendas externas como Docplanner, Google Calendar o Microsoft 365. Si TotalChat crea reservas sin consultar esas agendas, se pueden generar dobles reservas.

## Solución

Crear abstracciones:

```text
SchedulingProvider
MeetingProvider
```

Implementar inicialmente:

```text
InternalSchedulingProvider
ManualMeetingProvider
FakeSchedulingProvider para pruebas
```

## Requisitos funcionales

1. El tenant puede operar con agenda interna.
2. El tenant puede configurar proveedor externo futuro.
3. BookingService puede consultar disponibilidad mediante provider.
4. BookingService puede crear reserva mediante provider.
5. BookingService puede cancelar/reprogramar mediante provider.
6. El sistema puede guardar mappings externos.
7. El sistema puede registrar eventos externos.
8. El sistema puede registrar sync runs.
9. El sistema separa agenda de reunión virtual.

## Requisitos no funcionales

1. No acoplar core a Docplanner.
2. No permitir que LLM llame APIs externas directamente.
3. Toda integración debe mantener contexto tenant.
4. Deben existir tests con provider fake.
5. El MVP debe seguir funcionando sin proveedores externos.

## Fuera de alcance

- Implementación real Docplanner.
- Implementación real Google Calendar.
- Implementación real Microsoft.
- Sincronización bidireccional completa.



### plan.md

# Plan 011 — External Scheduling Provider Abstraction

## Componentes

- SchedulingProvider interface.
- MeetingProvider interface.
- InternalSchedulingProvider.
- ManualMeetingProvider.
- Provider registry.
- scheduling_provider_configs.
- meeting_provider_configs.
- external_systems.
- external mappings.
- external events.
- external sync runs.
- FakeSchedulingProvider.

## Interfaz sugerida

```python
class SchedulingProvider:
    def get_available_slots(self, request): ...
    def create_booking(self, request): ...
    def cancel_booking(self, request): ...
    def reschedule_booking(self, request): ...
    def get_booking(self, request): ...
    def sync_external_events(self, request): ...

class MeetingProvider:
    def create_meeting(self, request): ...
    def update_meeting(self, request): ...
    def cancel_meeting(self, request): ...
    def get_meeting_link(self, request): ...
```

## Riesgos

- Doble reserva.
- Complejidad excesiva temprana.
- Conflictos entre proveedor interno y externo.
- Mala configuración por tenant.

## Estrategia

Crear contratos y provider interno sin implementar proveedores externos reales todavía.



### tasks.md

# Tasks 011 — External Scheduling Provider Abstraction

- [ ] Definir `SchedulingProvider`.
- [ ] Definir `MeetingProvider`.
- [ ] Implementar `InternalSchedulingProvider`.
- [ ] Implementar `ManualMeetingProvider`.
- [ ] Crear `external_systems`.
- [ ] Crear `scheduling_provider_configs`.
- [ ] Crear `meeting_provider_configs`.
- [ ] Crear `external_practitioner_mappings`.
- [ ] Crear `external_location_mappings`.
- [ ] Crear `external_service_mappings`.
- [ ] Crear `external_booking_mappings`.
- [ ] Crear `external_events`.
- [ ] Crear `external_sync_runs`.
- [ ] Crear `FakeSchedulingProvider`.
- [ ] Ajustar BookingService para usar provider configurado.
- [ ] Ajustar cita virtual para usar MeetingProvider.
- [ ] Crear tests agenda interna.
- [ ] Crear tests provider fake.



### contracts.md

# Contracts — 011-external-scheduling-provider

Pendiente de completar durante la fase técnica.



### data-model.md

# Data-Model — 011-external-scheduling-provider

Pendiente de completar durante la fase técnica.



### quickstart.md

# Quickstart — 011-external-scheduling-provider

Pendiente de completar durante la fase técnica.



## 012-docplanner-adapter



### spec.md

# Spec 012 — Docplanner Scheduling Adapter

## Objetivo

Implementar Docplanner/Doctoralia como proveedor externo de agenda para tenants que ya usan ese sistema como agenda principal.

## Contexto

Docplanner puede manejar agenda médica, slots, bookings, doctores, direcciones, servicios y callbacks. Para TotalChat debe ser un adaptador, no el core.

## Requisitos funcionales

1. Configurar credenciales Docplanner por tenant.
2. Mapear doctores/profesionales.
3. Mapear sedes/direcciones/calendarios.
4. Mapear servicios.
5. Consultar slots disponibles.
6. Consultar bookings existentes.
7. Consultar breaks/bloqueos.
8. Crear booking externo.
9. Cancelar booking externo.
10. Reprogramar booking externo.
11. Procesar callbacks o pull notifications.
12. Guardar external_booking_mapping.
13. Registrar sync errors.

## Reglas

- Si Docplanner es autoridad, TotalChat no confirma localmente sin reserva externa.
- Docplanner no reemplaza pagos TotalChat.
- Docplanner no reemplaza precios jerárquicos TotalChat.
- Docplanner no reemplaza recordatorios TotalChat.
- Docplanner no reemplaza consola admin TotalChat.

## Fuera de alcance

- Convertir Docplanner en dependencia obligatoria.
- Reducir TotalChat al modelo Docplanner.
- Pagos Docplanner como core.



### plan.md

# Plan 012 — Docplanner Adapter

## Componentes

- Docplanner client.
- DocplannerSchedulingProvider.
- Auth/config por tenant.
- Resource mapping.
- Slot mapping.
- Booking mapping.
- Callback receiver.
- Sync jobs.
- Admin diagnostics.

## Flujos

1. Initial import.
2. Get slots.
3. Create booking.
4. Cancel booking.
5. Move booking.
6. External callback.
7. Manual reconciliation.

## Riesgos

- Cobertura API por país/cliente.
- Recursos no autorizados.
- Callbacks asíncronos.
- Conflictos con cambios directos en Docplanner.



### tasks.md

# Tasks 012 — Docplanner Adapter

- [ ] Crear Docplanner client.
- [ ] Configurar credenciales por tenant.
- [ ] Implementar DocplannerSchedulingProvider.
- [ ] Mapear doctores.
- [ ] Mapear direcciones/calendarios.
- [ ] Mapear servicios.
- [ ] Implementar get_available_slots.
- [ ] Implementar create_booking.
- [ ] Implementar cancel_booking.
- [ ] Implementar reschedule_booking.
- [ ] Implementar callbacks/pull notifications.
- [ ] Registrar external_events.
- [ ] Registrar sync_runs.
- [ ] Crear pantalla admin de mappings.
- [ ] Crear tests con mock API.



### contracts.md

# Contracts — 012-docplanner-adapter

Pendiente de completar durante la fase técnica.



### data-model.md

# Data-Model — 012-docplanner-adapter

Pendiente de completar durante la fase técnica.



### quickstart.md

# Quickstart — 012-docplanner-adapter

Pendiente de completar durante la fase técnica.



## 013-google-calendar-adapter



### spec.md

# Spec 013 — Google Calendar Scheduling Adapter

## Objetivo

Implementar Google Calendar como proveedor externo de agenda para tenants/profesionales que usan Google Calendar como calendario operativo.

## Requisitos funcionales

1. Configurar cuenta Google por tenant/profesional.
2. Mapear profesional a calendario.
3. Consultar disponibilidad/free-busy o eventos ocupados.
4. Crear evento para reserva.
5. Cancelar evento.
6. Reprogramar evento.
7. Guardar external_event_id.
8. Sincronizar cambios externos básicos.
9. Preparar integración futura con Google Meet.

## Reglas

- Si Google Calendar es autoridad, TotalChat no confirma sin crear/bloquear evento.
- Google Calendar no reemplaza pagos ni precios.
- Google Meet debe tratarse como MeetingProvider separado aunque se cree desde evento.



### plan.md

# Plan 013 — Google Calendar Adapter

## Componentes

- GoogleCalendar client.
- OAuth/service-account strategy.
- GoogleCalendarSchedulingProvider.
- Calendar mappings.
- Event mappings.
- Sync jobs.

## Riesgos

- Autorización OAuth.
- Calendarios compartidos.
- Eventos creados manualmente.
- Timezones.
- Reglas recurrentes.



### tasks.md

# Tasks 013 — Google Calendar Adapter

- [ ] Definir estrategia auth Google.
- [ ] Crear GoogleCalendar client.
- [ ] Mapear profesional a calendario.
- [ ] Implementar free/busy.
- [ ] Implementar create_event.
- [ ] Implementar cancel_event.
- [ ] Implementar update_event.
- [ ] Guardar external_event_id.
- [ ] Sincronizar eventos básicos.
- [ ] Preparar GoogleMeetProvider futuro.
- [ ] Crear tests con fake provider.



### contracts.md

# Contracts — 013-google-calendar-adapter

Pendiente de completar durante la fase técnica.



### data-model.md

# Data-Model — 013-google-calendar-adapter

Pendiente de completar durante la fase técnica.



### quickstart.md

# Quickstart — 013-google-calendar-adapter

Pendiente de completar durante la fase técnica.



## 014-microsoft-calendar-teams-adapter



### spec.md

# Spec 014 — Microsoft Calendar and Teams Adapter

## Objetivo

Implementar Microsoft 365 / Outlook Calendar como proveedor de agenda y Microsoft Teams como proveedor de reuniones virtuales.

## Requisitos funcionales

1. Configurar Microsoft Graph por tenant/profesional.
2. Mapear profesional a calendario Microsoft.
3. Consultar disponibilidad/eventos ocupados.
4. Crear evento Outlook.
5. Cancelar evento.
6. Reprogramar evento.
7. Crear reunión Teams cuando aplique.
8. Guardar external_event_id y meeting_url.
9. Sincronizar cambios básicos.

## Reglas

- Calendar provider y meeting provider son capas separadas.
- Teams no debe confundirse con agenda completa.
- Si Microsoft Calendar es autoridad, TotalChat no confirma sin crear/bloquear evento.



### plan.md

# Plan 014 — Microsoft Calendar and Teams Adapter

## Componentes

- Microsoft Graph client.
- MicrosoftCalendarSchedulingProvider.
- MicrosoftTeamsMeetingProvider.
- Calendar mappings.
- Event mappings.
- Meeting mappings.

## Riesgos

- Permisos Graph.
- Tenants Microsoft corporativos.
- Consentimiento administrativo.
- Timezones.
- Creación de Teams meeting.



### tasks.md

# Tasks 014 — Microsoft Calendar and Teams Adapter

- [ ] Definir estrategia Microsoft Graph.
- [ ] Crear Graph client.
- [ ] Implementar MicrosoftCalendarSchedulingProvider.
- [ ] Implementar MicrosoftTeamsMeetingProvider.
- [ ] Mapear calendarios.
- [ ] Implementar disponibilidad.
- [ ] Crear evento.
- [ ] Cancelar evento.
- [ ] Reprogramar evento.
- [ ] Crear Teams meeting.
- [ ] Guardar meeting_url.
- [ ] Crear tests con fake provider.



### contracts.md

# Contracts — 014-microsoft-calendar-teams-adapter

Pendiente de completar durante la fase técnica.



### data-model.md

# Data-Model — 014-microsoft-calendar-teams-adapter

Pendiente de completar durante la fase técnica.



### quickstart.md

# Quickstart — 014-microsoft-calendar-teams-adapter

Pendiente de completar durante la fase técnica.



## 015-campaigns-broadcast-messaging



### spec.md

# Spec 015 — Campaigns and Broadcast Messaging

## 1. Objetivo

Implementar el módulo transversal de campañas, comunicados y mensajería masiva de TotalChat.

El módulo debe permitir que un tenant envíe mensajes a sus contactos, pacientes, clientes o usuarios finales desde la consola administrativa, de forma inmediata o programada.

La primera implementación aplicará a MediChat, pero la arquitectura debe ser común para todos los verticales.

## 2. Contexto

TotalChat no solo debe responder conversaciones individuales o manejar reservas transaccionales. También debe permitir comunicaciones masivas controladas por el tenant.

Casos:

- publicidad;
- promociones;
- cierres temporales;
- cambios de horario;
- avisos operativos;
- apertura de agenda;
- recordatorios generales;
- comunicados segmentados.

## 3. Alcance funcional

Incluye:

1. Crear campañas.
2. Editar campañas en borrador.
3. Definir tipo de campaña.
4. Definir tipo de mensaje.
5. Seleccionar audiencia.
6. Previsualizar audiencia.
7. Previsualizar mensaje.
8. Enviar inmediatamente.
9. Programar envío.
10. Cancelar campaña programada.
11. Generar entregas individuales.
12. Procesar entregas.
13. Registrar estados de campaña.
14. Registrar estados de entrega.
15. Registrar métricas básicas.
16. Registrar auditoría.
17. Respetar preferencias de contacto.
18. Soportar Telegram inicialmente.
19. Dejar preparado WhatsApp futuro.
20. Permitir resolvers por vertical.

## 4. Fuera de alcance inicial

No incluir inicialmente:

- journeys multietapa;
- A/B testing;
- CRM avanzado;
- scoring de clientes;
- WhatsApp templates productivas;
- email marketing;
- SMS;
- adjuntos;
- diseño visual avanzado de campañas;
- automatizaciones complejas de marketing;
- IA generando mensajes sin revisión humana.

## 5. Verticales cubiertos

Diseño transversal:

```text
MediChat
RestoChat
HotelChat
StayChat
StoreChat
```

Implementación inicial:

```text
MediChat
```

## 6. Requisitos funcionales detallados

### 6.1. Crear campaña

El admin debe poder crear una campaña con:

```text
nombre
descripción
tipo de campaña
tipo de mensaje
vertical/solución
mensaje
audiencia
canal
modo de envío
```

### 6.2. Editar borrador

Mientras la campaña esté en `draft`, debe poder editarse.

### 6.3. Previsualizar audiencia

El sistema debe calcular:

```text
estimated_recipients
eligible_recipients
blocked_by_consent
blocked_by_channel_policy
blocked_by_missing_contact
```

### 6.4. Previsualizar mensaje

Antes de enviar debe mostrarse el mensaje final.

### 6.5. Enviar ahora

El admin debe confirmar explícitamente.

### 6.6. Programar envío

Debe soportar `scheduled_at` con timezone.

### 6.7. Cancelar campaña programada

Una campaña `scheduled` puede cancelarse antes de que pase a `sending`.

### 6.8. Registrar entregas

Cada destinatario genera una entrega.

### 6.9. Métricas

Debe mostrar conteos básicos.

### 6.10. Consentimiento

Marketing requiere `allow_marketing=true`.

## 7. Requisitos no funcionales

1. Multi-tenant estricto.
2. No mezclar datos entre tenants.
3. No depender de n8n como fuente de verdad.
4. Idempotencia para envíos.
5. Auditoría completa.
6. Rate limiting.
7. Manejo de errores por destinatario.
8. No enviar duplicados.
9. No bloquear la API durante envíos masivos.
10. Uso de worker/scheduler.

## 8. Reglas de dominio

1. Campaña sin audiencia válida no se envía.
2. Campaña sin mensaje no se envía.
3. Campaña de marketing sin consentimiento no se envía a ese contacto.
4. Delivery bloqueado por consentimiento debe quedar registrado.
5. Delivery fallido no debe detener necesariamente toda la campaña.
6. Campaña parcialmente fallida queda `partially_sent`.
7. Campaña programada debe poder cancelarse.
8. Campaña enviada no se edita.
9. n8n no decide destinatarios.
10. ChannelProvider ejecuta envío por canal.

## 9. Estados de campaña

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

## 10. Estados de entrega

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

## 11. Interfaz conceptual

```python
class CampaignService:
    def create_campaign(...): ...
    def update_campaign(...): ...
    def preview_audience(...): ...
    def schedule_campaign(...): ...
    def send_now(...): ...
    def cancel_campaign(...): ...

class AudienceResolver:
    def estimate(...): ...
    def resolve(...): ...

class CampaignDispatcher:
    def enqueue_deliveries(...): ...
    def process_delivery(...): ...
```

## 12. Resolvers por vertical

MVP:

```text
MediChatAudienceResolver
```

Futuro:

```text
RestoChatAudienceResolver
HotelChatAudienceResolver
StayChatAudienceResolver
StoreChatAudienceResolver
```

## 13. Riesgos

1. Enviar marketing sin consentimiento.
2. Duplicar mensajes.
3. Bloquear Telegram/WhatsApp por abuso.
4. Filtrar datos entre tenants.
5. Usar n8n como fuente de verdad.
6. No registrar errores individuales.
7. Enviar mensajes fuera de política del canal.
8. Permitir que IA envíe campañas sin revisión.

## 14. Criterios de aceptación

1. Existe módulo en admin para campañas.
2. Se puede crear campaña en draft.
3. Se puede previsualizar audiencia.
4. Se puede enviar ahora.
5. Se puede programar.
6. Se generan deliveries.
7. Se procesa delivery por Telegram fake/provider.
8. Se respetan preferencias.
9. Se registran métricas.
10. Se audita creación/envío/cancelación.
11. Tests cubren bloqueo por consentimiento.
12. Tests cubren campaña programada.
13. Tests cubren envío parcial.
14. Tests cubren multi-tenancy.
15. El módulo está en plataforma/core, no en MediChat.



### plan.md

# Plan 015 — Campaigns and Broadcast Messaging

## 1. Estrategia

Implementar el módulo en capas:

```text
packages/campaigns
packages/channels
packages/notifications
apps/api
apps/admin-web
apps/worker
solutions/medichat audience resolver
```

## 2. Componentes

### 2.1. Data model

Crear migraciones para:

```text
campaigns
campaign_audiences
campaign_recipients
campaign_deliveries
contact_preferences
campaign_templates
campaign_events
```

### 2.2. Domain services

Implementar:

```text
CampaignService
CampaignAudienceService
CampaignDeliveryPlanner
CampaignDispatcher
CampaignMetricsService
```

### 2.3. Audience resolver

Implementar:

```text
AudienceResolverRegistry
MediChatAudienceResolver
```

### 2.4. API

Implementar endpoints:

```text
POST /api/admin/campaigns
GET /api/admin/campaigns
GET /api/admin/campaigns/{campaign_id}
PATCH /api/admin/campaigns/{campaign_id}
POST /api/admin/campaigns/{campaign_id}/preview-audience
POST /api/admin/campaigns/{campaign_id}/schedule
POST /api/admin/campaigns/{campaign_id}/send-now
POST /api/admin/campaigns/{campaign_id}/cancel
GET /api/admin/campaigns/{campaign_id}/deliveries
GET /api/admin/campaigns/{campaign_id}/metrics
```

### 2.5. Worker

Implementar worker para:

```text
campaigns scheduled due
campaign deliveries queued
delivery retry if allowed
metrics aggregation
```

### 2.6. Admin web

Pantallas:

```text
Campaign list
Create campaign
Edit draft
Preview audience
Confirm send
Schedule send
Campaign detail
Delivery results
Metrics
```

## 3. Dependencias

- Multi-tenancy.
- Auth/admin users.
- Channels.
- Contacts/patients.
- Worker infrastructure.
- Audit events.
- Telegram provider o fake provider en pruebas.

## 4. Implementación recomendada por subfases

### 4.1. 015A — Modelo y servicios base

- Tablas.
- Estados.
- CampaignService.
- Tests de estado.

### 4.2. 015B — Audience resolver MediChat

- Resolver pacientes activos.
- Resolver pacientes por profesional.
- Resolver contactos por canal.
- Tests.

### 4.3. 015C — API Admin

- CRUD.
- preview audience.
- send-now.
- schedule.
- cancel.

### 4.4. 015D — Worker y deliveries

- Generar recipients.
- Generar deliveries.
- Procesar Telegram fake.
- Registrar estados.

### 4.5. 015E — Admin web

- Pantallas iniciales.
- Confirmación antes de envío.
- Métricas.

### 4.6. 015F — Hardening

- Idempotencia.
- Rate limits.
- Auditoría.
- Opt-out.
- Pruebas multi-tenant.

## 5. No desviación

No implementar:

- WhatsApp productivo.
- Email marketing.
- SMS.
- A/B testing.
- CRM avanzado.
- Adjuntos.
- IA enviando campañas automáticamente.



### tasks.md

# Tasks 015 — Campaigns and Broadcast Messaging

## 1. Documentación

- [ ] Revisar `docs/CAMPAIGNS_AND_BROADCASTS.md`.
- [ ] Revisar `docs/API_CONTRACTS.md`.
- [ ] Revisar `docs/STATE_MACHINES.md`.
- [ ] Revisar `docs/PR_REVIEW_CHECKLIST.md`.

## 2. Data model

- [ ] Crear tabla `campaigns`.
- [ ] Crear tabla `campaign_audiences`.
- [ ] Crear tabla `campaign_recipients`.
- [ ] Crear tabla `campaign_deliveries`.
- [ ] Crear tabla `contact_preferences`.
- [ ] Crear tabla `campaign_templates`.
- [ ] Crear tabla `campaign_events`.
- [ ] Agregar índices por tenant/campaign/status.
- [ ] Agregar timestamps.
- [ ] Agregar constraints de estados.

## 3. Domain

- [ ] Crear `CampaignService`.
- [ ] Crear `AudienceResolver` interface.
- [ ] Crear `AudienceResolverRegistry`.
- [ ] Crear `CampaignDeliveryPlanner`.
- [ ] Crear `CampaignDispatcher`.
- [ ] Crear `CampaignMetricsService`.
- [ ] Crear validaciones de consentimiento.
- [ ] Crear validaciones de canal.
- [ ] Crear validaciones de estado.

## 4. MediChat audience resolver

- [ ] Resolver todos los pacientes activos.
- [ ] Resolver pacientes por profesional.
- [ ] Resolver pacientes por servicio.
- [ ] Resolver pacientes por sede.
- [ ] Resolver pacientes con citas futuras.
- [ ] Resolver pacientes con canal Telegram.
- [ ] Aplicar preferencias de contacto.

## 5. API

- [ ] POST `/api/admin/campaigns`.
- [ ] GET `/api/admin/campaigns`.
- [ ] GET `/api/admin/campaigns/{campaign_id}`.
- [ ] PATCH `/api/admin/campaigns/{campaign_id}`.
- [ ] POST `/api/admin/campaigns/{campaign_id}/preview-audience`.
- [ ] POST `/api/admin/campaigns/{campaign_id}/schedule`.
- [ ] POST `/api/admin/campaigns/{campaign_id}/send-now`.
- [ ] POST `/api/admin/campaigns/{campaign_id}/cancel`.
- [ ] GET `/api/admin/campaigns/{campaign_id}/deliveries`.
- [ ] GET `/api/admin/campaigns/{campaign_id}/metrics`.

## 6. Worker

- [ ] Detectar campañas programadas vencidas.
- [ ] Encolar deliveries.
- [ ] Procesar deliveries.
- [ ] Manejar errores por delivery.
- [ ] Actualizar métricas.
- [ ] Garantizar idempotencia.

## 7. Admin web

- [ ] Menú `Campañas y comunicados`.
- [ ] Listado de campañas.
- [ ] Crear campaña.
- [ ] Editar borrador.
- [ ] Seleccionar audiencia.
- [ ] Preview de audiencia.
- [ ] Preview de mensaje.
- [ ] Enviar ahora.
- [ ] Programar.
- [ ] Cancelar programada.
- [ ] Ver resultados.
- [ ] Ver métricas.

## 8. Tests

- [ ] Crear campaña draft.
- [ ] Editar draft.
- [ ] Preview audiencia.
- [ ] Enviar campaña operativa.
- [ ] Bloquear marketing sin consentimiento.
- [ ] Generar deliveries.
- [ ] Procesar delivery exitoso.
- [ ] Procesar delivery fallido.
- [ ] Campaña parcialmente enviada.
- [ ] Campaña programada.
- [ ] Cancelar campaña programada.
- [ ] Multi-tenancy: campaña de tenant A no ve tenant B.
- [ ] Rate limit básico.
- [ ] Auditoría.

## 9. Seguridad y compliance

- [ ] Validar permisos admin.
- [ ] No exponer datos de otro tenant.
- [ ] No exponer tokens de canal.
- [ ] Auditar envío.
- [ ] Respetar opt-out.
- [ ] Confirmación explícita antes de enviar.



### contracts.md

# Contracts 015 — Campaigns and Broadcast Messaging

## 1. POST `/api/admin/campaigns`

Crea campaña en estado `draft`.

Request:

```json
{
  "name": "Cierre por vacaciones",
  "description": "Aviso operativo de cierre temporal",
  "campaign_type": "schedule_notice",
  "message_type": "operational",
  "solution_code": "medichat",
  "message_body": "Este fin de semana no tendremos servicio por temporada de vacaciones. Retomaremos atención el martes.",
  "audience_type": "all_active_patients",
  "audience_filters": {},
  "target_channel_policy": {
    "preferred_channels": ["telegram"],
    "fallback_channels": []
  }
}
```

Response:

```json
{
  "data": {
    "id": "uuid",
    "name": "Cierre por vacaciones",
    "status": "draft"
  }
}
```

## 2. GET `/api/admin/campaigns`

Lista campañas del tenant.

Query params:

```text
status
campaign_type
message_type
solution_code
page
page_size
```

## 3. GET `/api/admin/campaigns/{campaign_id}`

Detalle campaña.

## 4. PATCH `/api/admin/campaigns/{campaign_id}`

Solo permitido en estados editables:

```text
draft
ready
```

## 5. POST `/api/admin/campaigns/{campaign_id}/preview-audience`

Response:

```json
{
  "data": {
    "estimated_recipients": 120,
    "eligible_recipients": 105,
    "blocked_by_consent": 10,
    "blocked_by_channel_policy": 0,
    "blocked_by_missing_contact": 5
  }
}
```

## 6. POST `/api/admin/campaigns/{campaign_id}/schedule`

Request:

```json
{
  "scheduled_at": "2026-07-10T08:00:00-05:00",
  "timezone": "America/Bogota"
}
```

Response:

```json
{
  "data": {
    "id": "uuid",
    "status": "scheduled",
    "scheduled_at": "2026-07-10T08:00:00-05:00"
  }
}
```

## 7. POST `/api/admin/campaigns/{campaign_id}/send-now`

Request:

```json
{
  "confirm_send": true
}
```

Response:

```json
{
  "data": {
    "id": "uuid",
    "status": "queued"
  }
}
```

## 8. POST `/api/admin/campaigns/{campaign_id}/cancel`

Request:

```json
{
  "reason": "Cambio de decisión administrativa"
}
```

## 9. GET `/api/admin/campaigns/{campaign_id}/deliveries`

Response:

```json
{
  "data": [
    {
      "id": "uuid",
      "recipient_type": "patient",
      "recipient_id": "uuid",
      "channel_type": "telegram",
      "status": "sent",
      "sent_at": "2026-07-10T08:01:00-05:00"
    }
  ]
}
```

## 10. GET `/api/admin/campaigns/{campaign_id}/metrics`

Response:

```json
{
  "data": {
    "total_recipients": 120,
    "eligible_recipients": 105,
    "blocked_by_consent": 10,
    "blocked_by_missing_contact": 5,
    "queued_count": 0,
    "sent_count": 100,
    "failed_count": 5,
    "delivered_count": 0,
    "read_count": 0
  }
}
```

## 11. Errores

```text
VALIDATION_ERROR
AUTHORIZATION_FAILED
RESOURCE_NOT_FOUND
BUSINESS_RULE_VIOLATION
CAMPAIGN_NOT_EDITABLE
CAMPAIGN_ALREADY_SENT
AUDIENCE_EMPTY
CONSENT_REQUIRED
CHANNEL_POLICY_BLOCKED
RATE_LIMIT_EXCEEDED
```



### data-model.md

# Data Model 015 — Campaigns and Broadcast Messaging

## campaigns

```text
id
tenant_id
solution_code nullable
name
description nullable
campaign_type
message_type
status
send_mode
scheduled_at nullable
timezone
message_body
target_channel_policy
audience_type
audience_filters
estimated_recipients
eligible_recipients
blocked_recipients
created_by
approved_by nullable
approved_at nullable
sent_at nullable
cancelled_at nullable
created_at
updated_at
```

## campaign_audiences

```text
id
campaign_id
audience_type
filters
estimated_recipients
eligible_recipients
blocked_by_consent
blocked_by_channel_policy
blocked_by_missing_contact
created_at
updated_at
```

## campaign_recipients

```text
id
campaign_id
recipient_type
recipient_id
contact_id nullable
display_name nullable
channel_type
channel_address
consent_status
eligibility_status
eligibility_reason nullable
created_at
```

## campaign_deliveries

```text
id
campaign_id
campaign_recipient_id
recipient_type
recipient_id
channel_type
channel_address
status
provider_message_id nullable
error_code nullable
error_message nullable
queued_at nullable
sent_at nullable
delivered_at nullable
read_at nullable
failed_at nullable
created_at
updated_at
```

## contact_preferences

```text
id
tenant_id
solution_code nullable
contact_type
contact_id
channel_type
allow_transactional
allow_operational
allow_marketing
opted_out_at nullable
opt_out_reason nullable
source
created_at
updated_at
```

## campaign_templates

```text
id
tenant_id
solution_code nullable
name
description nullable
campaign_type
message_type
channel_type nullable
body_template
variables
status
created_by
created_at
updated_at
```

## campaign_events

```text
id
campaign_id
event_type
previous_status nullable
new_status nullable
actor_type
actor_id nullable
metadata
created_at
```

## Indexes recomendados

```text
campaigns(tenant_id, status)
campaigns(tenant_id, solution_code)
campaigns(tenant_id, scheduled_at)
campaign_deliveries(campaign_id, status)
campaign_deliveries(tenant_id, status) if tenant_id is denormalized
contact_preferences(tenant_id, contact_type, contact_id, channel_type)
```



### quickstart.md

# Quickstart 015 — Campaigns and Broadcast Messaging

## 1. Precondiciones

Debe existir:

- tenant activo;
- usuario admin;
- vertical MediChat activo;
- pacientes de prueba;
- contactos Telegram de prueba o provider fake;
- preferencias de contacto.

## 2. Crear campaña

```bash
curl -X POST http://localhost:8000/api/admin/campaigns \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -H "X-TotalChat-Tenant-Id: <tenant_id>" \
  -d '{
    "name": "Cierre por vacaciones",
    "description": "Aviso operativo",
    "campaign_type": "schedule_notice",
    "message_type": "operational",
    "solution_code": "medichat",
    "message_body": "Este fin de semana no tendremos servicio por temporada de vacaciones. Retomaremos atención el martes.",
    "audience_type": "all_active_patients",
    "audience_filters": {},
    "target_channel_policy": {
      "preferred_channels": ["telegram"],
      "fallback_channels": []
    }
  }'
```

## 3. Preview audiencia

```bash
curl -X POST http://localhost:8000/api/admin/campaigns/<campaign_id>/preview-audience \
  -H "Authorization: Bearer <token>" \
  -H "X-TotalChat-Tenant-Id: <tenant_id>"
```

## 4. Enviar ahora

```bash
curl -X POST http://localhost:8000/api/admin/campaigns/<campaign_id>/send-now \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -H "X-TotalChat-Tenant-Id: <tenant_id>" \
  -d '{"confirm_send": true}'
```

## 5. Programar

```bash
curl -X POST http://localhost:8000/api/admin/campaigns/<campaign_id>/schedule \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -H "X-TotalChat-Tenant-Id: <tenant_id>" \
  -d '{
    "scheduled_at": "2026-07-10T08:00:00-05:00",
    "timezone": "America/Bogota"
  }'
```

## 6. Validar métricas

```bash
curl http://localhost:8000/api/admin/campaigns/<campaign_id>/metrics \
  -H "Authorization: Bearer <token>" \
  -H "X-TotalChat-Tenant-Id: <tenant_id>"
```

## 7. Resultado esperado

- Campaña creada.
- Audiencia calculada.
- Entregas generadas.
- Entregas procesadas.
- Métricas visibles.
- Auditoría registrada.
- Marketing bloqueado si no hay consentimiento.
