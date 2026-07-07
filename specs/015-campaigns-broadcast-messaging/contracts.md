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
