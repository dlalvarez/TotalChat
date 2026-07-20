# Data Model — 005-langgraph-agent

Ver `docs/DATA_MODEL.md`. Detalles específicos se completarán durante esta spec.


## Fase 7A.1 — semantic_documents

La tabla `semantic_documents` se crea por schema tenant y no en `public`. Campos mínimos: `id`, `source_type`, `source_id`, `title`, `content`, `embedding VECTOR(TOTALCHAT_EMBEDDING_DIMENSIONS)`, `metadata`, `status`, `created_at`, `updated_at`. No incluye `schema_name`.
