# Quickstart 009 — Availability Slots

Consultar el endpoint admin autenticado con `GET /api/admin/availability/slots`, enviando el tenant seleccionado en `X-TotalChat-Tenant-Id` y los parámetros documentados en `contracts.md`. Una consulta no muta datos y nunca recibe `schema_name`.

Las reglas configuradas por el admin usan `0 = lunes` a `6 = domingo` y bastan para generar slots aunque el servicio no tenga filas en `service_modalities`. Una regla sin sede o consultorio devuelve esos recursos como `null`.
