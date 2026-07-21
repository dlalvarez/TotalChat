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
