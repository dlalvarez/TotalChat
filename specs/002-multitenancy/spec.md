# Spec 002 — Multi-Tenant Schema Architecture

## Objetivo

Implementar multi-tenancy por schema PostgreSQL.

## Alcance

- Schema public.
- Tenants.
- Tenant channels.
- Users.
- User tenants.
- Provisioning de schema.
- Tenant resolver.
- Tests de aislamiento.

## Requisitos

1. Crear tenant en `public.tenants`.
2. Crear schema asociado.
3. Aplicar migraciones base al schema.
4. Resolver tenant por canal.
5. Ejecutar operaciones dentro del schema correcto.
6. Prohibir herramientas sin contexto tenant.

## Criterios de aceptación

- Dos tenants pueden tener datos con mismos IDs lógicos sin mezclarse.
- Una consulta de tenant A no ve datos de tenant B.
- El resolver funciona por tenant_channel.
