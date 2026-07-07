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
