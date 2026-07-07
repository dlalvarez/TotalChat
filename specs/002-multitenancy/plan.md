# Plan 002 — Multi-Tenancy

## Diseño

Usar schema `public` para control y un schema por tenant.

## Componentes

- Tenant model.
- TenantChannel model.
- TenantProvisioningService.
- TenantResolver.
- TenantContext.
- Migration runner por schema.

## Validación

- Tests con tenant_a y tenant_b.
- Verificar aislamiento.
