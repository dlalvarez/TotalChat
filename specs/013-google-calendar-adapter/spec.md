# Spec 013 — Google Calendar Scheduling Adapter

## Objetivo

Implementar Google Calendar como proveedor externo de agenda para tenants/profesionales que usan Google Calendar como calendario operativo.

## Requisitos funcionales

1. Configurar cuenta Google por tenant/profesional.
2. Mapear profesional a calendario.
3. Consultar disponibilidad/free-busy o eventos ocupados.
4. Crear evento para reserva.
5. Cancelar evento.
6. Reprogramar evento.
7. Guardar external_event_id.
8. Sincronizar cambios externos básicos.
9. Preparar integración futura con Google Meet.

## Reglas

- Si Google Calendar es autoridad, TotalChat no confirma sin crear/bloquear evento.
- Google Calendar no reemplaza pagos ni precios.
- Google Meet debe tratarse como MeetingProvider separado aunque se cree desde evento.
