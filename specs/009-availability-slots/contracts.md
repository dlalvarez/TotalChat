# Contracts — 009 Availability Slots

`SchedulingProvider.get_available_slots(session, tenant_context, request)` recibe infraestructura tenant-scoped resuelta exclusivamente por el backend y un `AvailableSlotsRequest` con:

- `practitioner_service_id`;
- `date_from` y `date_to` inclusivos;
- `modality` (`in_person | virtual`);
- `practitioner_id`, `location_id` y `room_id` opcionales.

`location_id`, si se informa, debe identificar una sede activa de la organización del `practitioner_service`. `room_id` requiere `location_id` y debe identificar un consultorio activo que pertenezca a esa sede. La ausencia, inactividad o relación organizacional inconsistente de recursos explícitos se rechaza antes de consultar reglas o generar slots. El rango máximo es 31 días. El MVP usa `InternalSchedulingProvider` y retorna slots con inicio, fin, profesional, sede, consultorio, modalidad y `source=internal`. La equivalencia de deduplicación es inicio + fin + profesional + sede + consultorio + modalidad.

`availability_rules` es la fuente mínima de elegibilidad. `weekday` persiste la convención administrativa `0 = lunes` a `6 = domingo`. Una regla específica aplica a su servicio y una regla con `practitioner_service_id = null` aplica a todos los servicios compatibles del profesional. La modalidad se resuelve desde la regla: `both` admite `in_person` y `virtual`; las modalidades específicas solo admiten su igual. `service_modalities` no es requisito para generar slots en esta fase. Una regla sin sede o consultorio produce disponibilidad general con esos campos en `null`.

`GET /api/admin/availability/slots` conserva `payer_plan_id` solo por compatibilidad; no ejecuta precios ni cobertura. Responde `{"data": []}` sin disponibilidad y `VALIDATION_ERROR` para rangos inválidos. Los UUIDs son referencias operativas del admin; nunca se devuelve `schema_name`.

Las reglas recurrentes usan horas locales sin zona tenant formal, según el patrón backend existente. No se inventa offset. El contrato no está disponible como tool del runtime conversacional en esta fase.
