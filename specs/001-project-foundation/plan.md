# Plan 001 — Project Foundation

## Stack

- FastAPI.
- SQLAlchemy.
- Alembic.
- PostgreSQL + pgvector.
- Redis.
- React + Vite.
- Docker Compose.

## Pasos

1. Crear estructura repo.
2. Crear backend FastAPI.
3. Crear frontend Vite.
4. Crear Dockerfile backend.
5. Crear Dockerfile frontend si aplica.
6. Crear docker-compose.
7. Configurar PostgreSQL.
8. Habilitar pgvector.
9. Configurar Redis.
10. Crear healthcheck.
11. Crear tests.
12. Actualizar docs.

## Riesgos

- Complejidad inicial excesiva.
- Configuración de pgvector.
- Incompatibilidades Docker.

## Validación

- Levantar stack.
- Ejecutar tests.
- Verificar health.
