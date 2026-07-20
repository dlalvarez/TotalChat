# Contracts — 005-langgraph-agent

Pendiente de definir endpoints/API contracts durante el plan técnico.


## Fase 7A.1

No se agregan endpoints HTTP ni contratos de canal. Los contratos internos nuevos son `LLMProvider`, `EmbeddingsProvider` y `OpenAIProvider`, todos bajo tenant ya resuelto por backend para usos futuros.

## Fase 7A.1.1

`OpenAICompatibleProvider` implementa los contratos internos para OpenAI y DeepInfra/Qwen mediante configuración genérica. Devuelve `LLMResponse(content, model, provider, metadata)` con `content` solo desde `choices[0].message.content`. `reasoning_content` es metadata técnica opcional: se excluye por defecto y solo se captura con `TOTALCHAT_LLM_CAPTURE_REASONING=true`; nunca es respuesta visible, no se expone a frontend/canales, no se persiste ni gobierna lógica de negocio, tools, pagos, citas, disponibilidad, autorización o tenant. La factory selecciona provider antes de cualquier LangGraph futuro. No se agregan endpoints HTTP, fallback automático, configuración por tenant ni exposición de `schema_name`.

LLM y embeddings pueden usar proveedores distintos. La configuración operativa documentada combina LLM DeepInfra/Qwen con embeddings OpenAI `text-embedding-3-small` y `TOTALCHAT_EMBEDDING_DIMENSIONS=1536`. Adoptar otro modelo, incluido DeepInfra/Qwen Embedding, requiere verificar su dimensión real antes de persistir vectores o modificar la columna `semantic_documents.embedding VECTOR(...)`; no es un cambio trivial de configuración.
