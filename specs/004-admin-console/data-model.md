# Data Model — 004-admin-console

Ver `docs/DATA_MODEL.md`. Detalles específicos se completarán durante esta spec.

## Fase 6B.5

La consola administra `organization_practitioners` como relación muchos-a-muchos tenant entre `organizations` y `practitioners`, con `role`, `status`, timestamps y restricción única por pareja. Servicios queda para Fase 6B.6 y deberá validar esta relación activa.


## Fase 6B.6 — PractitionerService

La consola administra `PractitionerService` por organización y profesional. La pareja depende de `organization_practitioners` activa para creación/reactivación. Los servicios históricos permanecen listables con padres o relación inactivos. No hay `service_catalog_id`, `price`, `modality`, `availability`, `specialty_id`, `location_id` ni `room_id` en esta fase.
