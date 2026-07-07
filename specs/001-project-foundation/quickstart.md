# Quickstart — Spec 001 Project Foundation

## Objetivo

Validar que la fundación técnica de TotalChat levanta correctamente.

## Pasos esperados

```bash
cp .env.example .env
docker compose up --build
```

Validar backend:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

Ejecutar pruebas:

```bash
cd backend
pytest
```

Validar frontend:

```bash
cd frontend
npm install
npm run dev
```

## Resultado esperado

- Backend responde health.
- PostgreSQL está disponible.
- Redis está disponible.
- Frontend carga pantalla base.
- No existen funcionalidades de negocio todavía.
