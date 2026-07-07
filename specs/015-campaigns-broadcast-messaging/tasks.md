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
