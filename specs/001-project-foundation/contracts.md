# Contracts — Spec 001 Project Foundation

## Endpoints

### GET /health

Debe responder si el backend está vivo.

Response:

```json
{
  "data": {
    "status": "ok",
    "service": "totalchat-api",
    "version": "0.1.0"
  }
}
```

### GET /ready

Debe validar dependencias mínimas.

Response:

```json
{
  "data": {
    "status": "ready",
    "database": "ok",
    "redis": "ok"
  }
}
```

## Reglas

- No implementar dominio de negocio en esta spec.
- No implementar Telegram en esta spec.
- No implementar pagos en esta spec.
- No implementar LangGraph completo en esta spec.
- Sí dejar estructura preparada para módulos futuros.

## Validación

- `docker compose up` levanta servicios.
- `/health` responde 200.
- `/ready` responde 200 cuando PostgreSQL y Redis están disponibles.
- Tests base pasan.
