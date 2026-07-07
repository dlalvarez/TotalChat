# Spec 006 — Telegram Channel

## Objetivo

Conectar TotalChat a Telegram.

## Alcance

- Webhook.
- Tenant resolver por canal.
- Persistencia de mensajes.
- Envío de respuestas.
- Flujo de reserva básico.

## Criterios

- Mensaje entrante se asocia al tenant.
- Se crea sesión.
- Se invoca agente.
- Se responde al usuario.
