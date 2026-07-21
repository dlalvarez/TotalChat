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
