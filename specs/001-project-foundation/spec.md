# Spec 001 — Project Foundation

## Objetivo

Crear la base técnica del proyecto TotalChat.

## Alcance

Incluye:

- Estructura de repo.
- Backend FastAPI.
- Frontend admin base.
- Docker Compose.
- PostgreSQL.
- pgvector.
- Redis.
- Healthchecks.
- Configuración.
- Logging.
- Documentación base.

No incluye:

- Dominio de reservas.
- Telegram.
- Pagos.
- LangGraph completo.

## Requisitos funcionales

1. El backend debe iniciar.
2. Debe existir `GET /health`.
3. Docker Compose debe levantar backend, postgres y redis.
4. PostgreSQL debe tener pgvector habilitado.
5. El frontend debe iniciar como app base.
6. Debe existir `.env.example`.
7. Deben existir docs iniciales.

## Requisitos no funcionales

- Configuración por variables de entorno.
- Logs básicos.
- Pruebas mínimas.
- Preparado para Linux/Docker.

## Criterios de aceptación

- `docker compose up` levanta servicios.
- `/health` responde OK.
- Redis responde.
- PostgreSQL responde.
- pgvector está disponible.
- Tests base pasan.
