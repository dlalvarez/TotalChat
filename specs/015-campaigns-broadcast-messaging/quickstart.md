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
