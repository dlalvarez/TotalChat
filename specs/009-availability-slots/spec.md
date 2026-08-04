# Spec 009 — Availability Slots

## Objetivo

Implementar la Fase 8A.10: consulta interna, tenant-scoped y de solo lectura de slots reales mediante `SchedulingProvider`, sin conectar todavía la capacidad al runtime conversacional.

## Alcance

- Fortalecer `InternalSchedulingProvider` como autoridad MVP.
- Generar slots desde reglas activas, vigencia y duración del servicio, sin
  exigir filas en `service_modalities`.
- Usar la convención administrativa `weekday` de `0 = lunes` a `6 = domingo`.
- Aplicar modalidad, profesional, sede y consultorio.
- Excluir excepciones activas y bookings bloqueantes solapados.
- Deduplicar slots equivalentes y limitar consultas a 31 días inclusivos.
- Mantener el endpoint admin existente sin exponer `schema_name`.

## Exclusiones

Reservas, holds, confirmación, cancelación, reprogramación, pagos, tool conversacional, LangGraph, proveedores externos, MeetingProvider y frontend nuevo.
