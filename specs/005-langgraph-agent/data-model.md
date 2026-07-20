# Data Model — 005-langgraph-agent

Ver `docs/DATA_MODEL.md`. Detalles específicos se completarán durante esta spec.


## Fase 7A.1 — semantic_documents

La tabla `semantic_documents` se crea por schema tenant y no en `public`. Campos mínimos: `id`, `source_type`, `source_id`, `title`, `content`, `embedding VECTOR(TOTALCHAT_EMBEDDING_DIMENSIONS)`, `metadata`, `status`, `created_at`, `updated_at`. No incluye `schema_name`.

## Fase 7A.2 — estado conversacional base

`BookingConversationState` es un modelo interno temporal, validado y serializable a JSON para una integración futura con Redis. Conserva identificadores internos de conversación y tenant ya resuelto, referencias opcionales a paciente, servicio, profesional, sede/consultorio, modalidad, pagador/plan, slot, reserva e intento de pago, además de etapa, intención, campos pendientes y un contexto mínimo de mensajes.

El estado no es fuente de verdad y no valida entidades contra PostgreSQL. No contiene `schema_name` ni `reasoning_content`; rechaza campos desconocidos y claves sensibles o de infraestructura dentro de `metadata`. Esta fase no persiste el modelo, no ejecuta LangGraph y no implementa tools ni transiciones del dominio.
