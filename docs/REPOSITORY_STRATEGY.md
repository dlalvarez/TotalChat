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
- OpenAICompatibleProvider;
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
