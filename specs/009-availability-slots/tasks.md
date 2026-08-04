# Tasks 009 — Availability Slots

- [x] Definir request explícito de `SchedulingProvider.get_available_slots`.
- [x] Usar `InternalSchedulingProvider` desde el endpoint admin.
- [x] Validar rango, modalidad, sede activa de la organización y pertenencia del consultorio activo a la sede.
- [x] Generar por duración y vigencia desde reglas activas.
- [x] Usar la convención admin de weekday `0=lunes` a `6=domingo`.
- [x] Generar desde reglas sin exigir filas en `service_modalities`.
- [x] Admitir reglas generales por servicio y recursos opcionales.
- [x] Excluir excepciones activas y bookings bloqueantes solapados.
- [x] Preservar bookings terminales como no bloqueantes.
- [x] Deduplicar y ordenar slots equivalentes.
- [x] Probar filtros, respuesta vacía, contrato HTTP y ausencia de `schema_name`.
- [x] Documentar zona horaria, `payer_plan_id` y exclusiones.
