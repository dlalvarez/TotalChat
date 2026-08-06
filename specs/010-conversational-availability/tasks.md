# Tasks 010 — Conversational Availability

- [x] Agregar tool cerrada `get_available_slots` y sanitizar resultados.
- [x] Exigir servicio confirmado y usar su ID solo internamente.
- [x] Interpretar hoy, mañana, días próximos y preferencias horarias simples.
- [x] Limitar rango a 31 días inclusivos y salida visible a diez slots.
- [x] Persistir solo resumen seguro de la última consulta.
- [x] Bloquear intentos de reserva, holds y pagos.
- [x] Mantener Telegram sobre el invoker común.
- [x] Cubrir parser, autorización, sanitización, truncado y bloqueo.
- [x] Delegar la redacción normal al runtime desde payloads grounded y eliminar
  libretos conversacionales de disponibilidad del invoker.
