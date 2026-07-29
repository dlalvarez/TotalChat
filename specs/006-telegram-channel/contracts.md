# Contracts — 006-telegram-channel

## Fase 8A.1 — Entrada

`POST /api/webhooks/telegram/{webhook_secret}` compara el secreto con
`TOTALCHAT_TELEGRAM_WEBHOOK_SECRET`. El backend resuelve el canal activo mediante
`TOTALCHAT_TELEGRAM_BOT_IDENTIFIER`; el payload y el LLM nunca seleccionan tenant
ni schema. `TOTALCHAT_TELEGRAM_BOT_TOKEN` queda configurado por entorno para una
fase saliente posterior y no se usa en 8A.1.

La entrada soporta `update_id` y un mensaje de texto con `message_id`, `chat.id` y
`text`. Un canal sin tenant activo recibe `200 {"ok": true}` sin escritura tenant;
un secreto inválido recibe `404`. Para un canal válido, se crea o reutiliza una
sesión tenant-scoped y se persiste el mensaje `incoming`. `update_id` es el
identificador idempotente. Solo se guardan identificadores técnicos mínimos, sin
secretos, perfil de usuario ni `schema_name`.

Exclusiones: Booking Agent/LLM, red, cliente Telegram, mensajes salientes,
comandos y lógica de reservas o pagos.

## Fase 8A.2 — Puente interno al Booking Agent

Después de persistir y confirmar el mensaje `incoming`, el servicio construye una
`BookingConversationRequest` con una lista cerrada de campos del estado de la
sesión tenant-scoped y el texto recibido como consulta de servicio. El `tenant_id`
proviene exclusivamente del resolver de canal. El puente instancia las tools SQL
tenant-scoped y ejecuta el `BookingAgent` determinístico de 7A.9.

El resultado se guarda como un `Message(direction="outgoing")` interno con
`delivery_status="pending"`. Este estado significa generado pero **no enviado**.
Los errores controlados también dejan una respuesta interna genérica pendiente y
no cambian el `200` del webhook; no se persisten detalles de excepción. Un update
duplicado no vuelve a invocar el agente.

Exclusiones: cliente o API saliente de Telegram, red, LLM/provider, LangGraph
runtime y cualquier estado `sent` o confirmación de entrega.

## Fase 8A.3 — Entrega saliente controlada

Después de persistir el mensaje `outgoing` con estado `pending`, el backend usa
el token configurado por entorno para llamar `sendMessage`. Solo una confirmación
válida de Telegram cambia el estado a `sent`; una excepción de red o respuesta no
confirmada cambia el estado a `failed` sin alterar la respuesta exitosa del
webhook. Un update ya procesado no vuelve a invocar el agente ni a entregar el
mensaje. El token, `schema_name` y los detalles de excepciones no se persisten ni
se incluyen en respuestas.

Exclusiones: reintentos, jobs, colas, LLM, LangGraph runtime y otros canales.

## Fase 8A.4 — Contrato común de canales

Telegram es el primer adaptador concreto de un flujo conversacional propiedad del
backend; no es el modelo del core. Cada adaptador futuro deberá traducir su
payload externo a los conceptos internos existentes (`channel_type`, sesión de
conversación, mensaje, `direction` y estado de entrega) y conservar sus campos,
credenciales y confirmaciones de transporte dentro del límite del adaptador.

El límite común de invocación al agente es `ConversationAgentInvoker`: recibe
exclusivamente el `tenant_id` ya resuelto por el backend, la conversación
tenant-scoped y el texto normalizado. No recibe payloads, tokens, chat IDs,
`schema_name` ni tipos de Telegram. El adaptador es responsable de la entrada,
la idempotencia del identificador externo y la traducción de la confirmación de
entrega a `pending`, `sent` o `failed`; el agente no conoce esos detalles.

Flujo obligatorio:

```text
canal externo
  -> adaptador concreto
  -> resolución backend de tenant
  -> conversación/mensaje tenant-scoped
  -> ConversationAgentInvoker
  -> mensaje outgoing pending
  -> transporte del adaptador
  -> sent | failed
```

Un canal futuro debe implementar estas fronteras sin copiar reservas, precios,
disponibilidad, pagos ni selección de tenant al adaptador. Esta fase no agrega
canales, endpoints, runtime LLM/LangGraph, colas, jobs ni reintentos y no modifica
el flujo observable de Telegram 8A.1–8A.3.

## Fase 8A.5 — Respuesta inicial con contexto incompleto

Cuando `conversation_sessions.state` no contiene el contexto mínimo requerido
por el agente determinístico, el backend no lo invoca ni expone su fallback
técnico. Actualiza el estado tenant-scoped con la fase
`collecting_booking_context`, el último texto recibido y la lista de campos
faltantes, y genera una respuesta conversacional que solicita el servicio.

El estado previo permitido se conserva y la respuesta se persiste y entrega con
la semántica `pending` → `sent | failed` existente. Ni el estado ni el texto
visible incluyen `schema_name`, UUIDs, precios, disponibilidad o citas inventadas.
Esta fase no interpreta intención ni completa el flujo natural de reserva.

## Fase 8A.6 — frontera conversacional grounded (documental)

8A.5 permanece válida como implementación transitoria: probó estado incompleto,
persistencia y entrega, pero su texto fijo no es el diseño conversacional
definitivo. 8A.6 no modifica ese código. Una fase posterior reemplazará la
redacción normal hardcodeada por generación LLM y conservará idempotencia,
persistencia y la semántica `pending → sent | failed`.

Telegram continúa siendo solo el primer adaptador. Recibe, normaliza, persiste,
invoca `ConversationAgentInvoker` y entrega; no interpreta intención, selecciona
tools, consulta dominio, crea reservas o pagos, redacta diálogo ni resuelve tenant
desde texto del usuario. `ConversationAgentInvoker` sigue agnóstico del canal y
provider concreto.

El futuro input conceptual del agente recibe tenant interno ya resuelto,
conversación tenant-scoped, texto normalizado, contexto seguro y catálogo de
tools. No recibe payload externo completo, chat ID, token, `schema_name`, API keys
o secretos. La salida conversacional natural pertenece al LLM; tools y backend
solo retornan resultados estructurados o fallbacks técnicos controlados.

El contrato detallado, incluida la prohibición de libretos normales y la
secuencia de tool calling, está en
[`docs/CONVERSATION_ORCHESTRATION.md`](../../docs/CONVERSATION_ORCHESTRATION.md).
Esta fase no introduce runtime, modelos, prompts, tools, endpoints ni cambios de
Telegram.

## Fase 8A.7 — runtime conversacional natural básico

Telegram invoca siempre `ConversationAgentInvoker` después de hacer durable el
incoming. Su implementación natural carga historial reciente tenant-scoped,
invoca el runtime basado en `LLMProvider` y devuelve el texto visible completo.
El adaptador lo persiste sin reescritura como `outgoing/pending` y conserva la
entrega `sent | failed`. Un update duplicado termina antes de invocar o entregar.

La respuesta fija normal de 8A.5 deja de ser una ruta de ejecución. Solo se
permite el fallback técnico genérico ante fallos o contenido inválido. Telegram
no contiene prompts ni configuración LLM y al runtime no llegan token, chat ID,
payload completo o schema. Esta fase no conecta tools ni datos operacionales.

El historial del invoker se forma exclusivamente con incoming anteriores y
outgoing confirmados `sent`; `pending`, `failed`, direcciones desconocidas y la
entrada actual quedan fuera. El límite de ocho se aplica después de ese filtro.
La identidad Sofía/Sofi predeterminada y cualquier alternativa backend-owned no
son responsabilidad ni configuración de Telegram.
El invoker obtiene ese historial mediante lectura descendente en lotes limitados
y keyset `(created_at, id)`, deteniéndose al reunir ocho visibles o agotar el
historial. No carga toda la conversación ni usa `OFFSET`.

## Fase 8A.8 — tool calling tenant-scoped de servicios

El invoker común habilita el catálogo cerrado con una única tool de lectura:
`search_services({query?})`. La sesión ya seleccionada por el resolver constituye
el contexto tenant; tenant y `schema_name` nunca son argumentos del LLM. El
backend valida la solicitud, consulta `practitioner_services` mediante la capa de
servicios existente y entrega al LLM únicamente nombre, descripción y duración.
El LLM genera la respuesta visible final.

Telegram no conoce el catálogo, los argumentos ni los resultados. Continúa
limitándose a persistencia, invocación y entrega. No se habilitan precios,
disponibilidad, reservas, pagos ni otras tools.
