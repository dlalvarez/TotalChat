# Data Model — 004-admin-console

Ver `docs/DATA_MODEL.md`. Detalles específicos se completarán durante esta spec.

## Fase 6B.5

La consola administra `organization_practitioners` como relación muchos-a-muchos tenant entre `organizations` y `practitioners`, con `role`, `status`, timestamps y restricción única por pareja. Servicios queda para Fase 6B.6 y deberá validar esta relación activa.


## Fase 6B.6 — PractitionerService

La consola administra `PractitionerService` por organización y profesional. La pareja depende de `organization_practitioners` activa para creación/reactivación. Los servicios históricos permanecen listables con padres o relación inactivos. No hay `service_catalog_id`, `price`, `modality`, `availability`, `specialty_id`, `location_id` ni `room_id` en esta fase.

## Fase 6B.7 — PayerType, Payer y PayerPlan

La consola administra `payer_types`, `payers` y `payer_plans` como base comercial previa a tarifas. `PayerType` usa `code`, `name`, `description` y `status`; `code` se normaliza y es único de forma case-insensitive en la aplicación. `Payer` depende de `payer_type_id` y valida nombre único normalizado por tipo. `PayerPlan` depende de `payer_id` y valida nombre único normalizado por pagador.

Crear o reactivar pagadores requiere tipo activo. Crear o reactivar planes requiere pagador activo y tipo activo. No hay borrado físico y los registros históricos siguen listables aunque sus padres queden inactivos. No se implementan precios ni `PractitionerServicePrice` en esta fase.
