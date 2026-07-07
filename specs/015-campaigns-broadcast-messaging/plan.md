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
