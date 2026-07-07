# Spec 008 — Reminders and Attendance Confirmation

## Objetivo

Implementar recordatorios y confirmación de asistencia.

## Reglas

- Enviar recordatorio por mismo canal.
- Confirmación positiva mantiene cita.
- Respuesta negativa requiere segunda confirmación.
- No respuesta según política tenant.
- Reembolso según política.

## Criterios

- Reminder se genera.
- Usuario confirma.
- Usuario declina y confirma cancelación.
- Slot se libera tras cancelación confirmada.
