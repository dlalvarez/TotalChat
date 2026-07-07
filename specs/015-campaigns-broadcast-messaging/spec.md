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
