# Contracts — 010 Conversational Availability

`get_available_slots` acepta únicamente `date_from`, `date_to`, `modality` y los
filtros horarios opcionales `time_from`/`time_to`. El backend añade el
`selected_service.id` confirmado y el `TenantContext` ya resuelto; la tool nunca
acepta `schema_name`, tenant, UUID de servicio, sede o consultorio desde el LLM.

La respuesta contiene nombre legible del servicio, rango, modalidad y slots con
`date`, `start_time` y `end_time`. No contiene UUID, `schema_name`, precios ni
payloads internos. El usuario ve hasta diez inicios y una indicación si existen
más. Un resultado vacío no inventa horarios.

Sin servicio confirmado o fecha inequívoca no se consulta el provider. La
modalidad predeterminada es `in_person`; una mención virtual usa `virtual`.
Pedidos de sede o consultorio no se resuelven en esta fase. Intentos de reservar
después de consultar se bloquean con respuesta backend-owned.

El resultado grounded incluye `kind`, `status`, `total_slots`, `shown_slots`,
`has_more` y límites booleanos para reserva, hold y pago. El backend decide y
ejecuta; el LLM redacta la respuesta final desde este payload. Los bloqueos por
servicio o fecha usan `kind` y `reason` estructurados, sin ejecutar la tool.
