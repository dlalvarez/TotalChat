# Contracts — 009 Availability Slots

`SchedulingProvider.get_available_slots(session, tenant_context, request)` recibe infraestructura tenant-scoped resuelta exclusivamente por el backend y un `AvailableSlotsRequest` con:

- `practitioner_service_id`;
- `date_from` y `date_to` inclusivos;
- `modality` (`in_person | virtual`);
- `practitioner_id`, `location_id` y `room_id` opcionales.

`room_id` requiere `location_id`. El rango máximo es 31 días. El MVP usa `InternalSchedulingProvider` y retorna slots con inicio, fin, profesional, sede, consultorio, modalidad y `source=internal`. La equivalencia de deduplicación es inicio + fin + profesional + sede + consultorio + modalidad.

`GET /api/admin/availability/slots` conserva `payer_plan_id` solo por compatibilidad; no ejecuta precios ni cobertura. Responde `{"data": []}` sin disponibilidad y `VALIDATION_ERROR` para rangos inválidos. Los UUIDs son referencias operativas del admin; nunca se devuelve `schema_name`.

Las reglas recurrentes usan horas locales sin zona tenant formal, según el patrón backend existente. No se inventa offset. El contrato no está disponible como tool del runtime conversacional en esta fase.
