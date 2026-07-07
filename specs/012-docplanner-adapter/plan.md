# Plan 012 — Docplanner Adapter

## Componentes

- Docplanner client.
- DocplannerSchedulingProvider.
- Auth/config por tenant.
- Resource mapping.
- Slot mapping.
- Booking mapping.
- Callback receiver.
- Sync jobs.
- Admin diagnostics.

## Flujos

1. Initial import.
2. Get slots.
3. Create booking.
4. Cancel booking.
5. Move booking.
6. External callback.
7. Manual reconciliation.

## Riesgos

- Cobertura API por país/cliente.
- Recursos no autorizados.
- Callbacks asíncronos.
- Conflictos con cambios directos en Docplanner.
