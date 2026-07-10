# Data Model — 004-admin-console

Ver `docs/DATA_MODEL.md`. Detalles específicos se completarán durante esta spec.

## Fase 6B.5

La consola administra `organization_practitioners` como relación muchos-a-muchos tenant entre `organizations` y `practitioners`, con `role`, `status`, timestamps y restricción única por pareja. Servicios queda para Fase 6B.6 y deberá validar esta relación activa.
