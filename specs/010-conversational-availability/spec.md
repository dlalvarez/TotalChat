# Spec 010 — Conversational Availability

## Objetivo

Implementar la Fase 8A.11: consulta conversacional tenant-scoped y de solo
lectura de slots reales desde la capacidad validada en 8A.10.

## Alcance

- Exponer `get_available_slots` en el catálogo cerrado común.
- Exigir servicio backend-owned confirmado.
- Interpretar conservadoramente fechas y preferencias horarias simples.
- Consultar `SchedulingProvider` con rango inclusivo máximo de 31 días.
- Mostrar como máximo diez horas legibles y persistir solo el resumen seguro.
- Compartir el invoker con Telegram sin lógica de canal propia.
- Entregar al LLM un resultado estructurado sanitizado para que redacte la
  respuesta normal; no construir libretos de disponibilidad en Python.

## Exclusiones

Selección definitiva de slot, reservas, holds, bloqueos, confirmaciones,
reprogramaciones, cancelaciones, precios, pagadores, pagos, integraciones
externas, frontend y LangGraph.
