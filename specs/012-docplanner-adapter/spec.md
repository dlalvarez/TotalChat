# Spec 012 — Docplanner Scheduling Adapter

## Objetivo

Implementar Docplanner/Doctoralia como proveedor externo de agenda para tenants que ya usan ese sistema como agenda principal.

## Contexto

Docplanner puede manejar agenda médica, slots, bookings, doctores, direcciones, servicios y callbacks. Para TotalChat debe ser un adaptador, no el core.

## Requisitos funcionales

1. Configurar credenciales Docplanner por tenant.
2. Mapear doctores/profesionales.
3. Mapear sedes/direcciones/calendarios.
4. Mapear servicios.
5. Consultar slots disponibles.
6. Consultar bookings existentes.
7. Consultar breaks/bloqueos.
8. Crear booking externo.
9. Cancelar booking externo.
10. Reprogramar booking externo.
11. Procesar callbacks o pull notifications.
12. Guardar external_booking_mapping.
13. Registrar sync errors.

## Reglas

- Si Docplanner es autoridad, TotalChat no confirma localmente sin reserva externa.
- Docplanner no reemplaza pagos TotalChat.
- Docplanner no reemplaza precios jerárquicos TotalChat.
- Docplanner no reemplaza recordatorios TotalChat.
- Docplanner no reemplaza consola admin TotalChat.

## Fuera de alcance

- Convertir Docplanner en dependencia obligatoria.
- Reducir TotalChat al modelo Docplanner.
- Pagos Docplanner como core.
