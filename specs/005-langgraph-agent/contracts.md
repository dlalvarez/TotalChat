# Contracts — 005-langgraph-agent

Pendiente de definir endpoints/API contracts durante el plan técnico.


## Fase 7A.1

No se agregan endpoints HTTP ni contratos de canal. Los contratos internos nuevos son `LLMProvider`, `EmbeddingsProvider` y `OpenAICompatibleProvider`, todos bajo tenant ya resuelto por backend para usos futuros.

## Fase 7A.1.1

`OpenAICompatibleProvider` implementa los contratos internos para OpenAI y DeepInfra/Qwen mediante configuración genérica. Devuelve `LLMResponse(content, model, provider, metadata)` con `content` solo desde `choices[0].message.content`. `reasoning_content` es metadata técnica opcional: se excluye por defecto y solo se captura con `TOTALCHAT_LLM_CAPTURE_REASONING=true`; nunca es respuesta visible, no se expone a frontend/canales, no se persiste ni gobierna lógica de negocio, tools, pagos, citas, disponibilidad, autorización o tenant. La factory selecciona provider antes de cualquier LangGraph futuro. No se agregan endpoints HTTP, fallback automático, configuración por tenant ni exposición de `schema_name`.

`TOTALCHAT_LLM_API_KEY` es la única variable de credencial LLM para OpenAI, DeepInfra/Qwen, Kimi futuro y cualquier proveedor OpenAI-compatible. No existe fallback ni compatibilidad con variables de credencial específicas de proveedor.

No existe una clase concreta especial para OpenAI ni para otro proveedor. OpenAI, DeepInfra/Qwen y Kimi futuro son configuraciones de `OpenAICompatibleProvider`; toda integración futura consume `LLMProvider`/`EmbeddingsProvider` mediante las factories internas.

LLM y embeddings pueden usar proveedores distintos. La configuración operativa documentada combina LLM DeepInfra/Qwen con embeddings OpenAI `text-embedding-3-small` y `TOTALCHAT_EMBEDDING_DIMENSIONS=1536`. Adoptar otro modelo, incluido DeepInfra/Qwen Embedding, requiere verificar su dimensión real antes de persistir vectores o modificar la columna `semantic_documents.embedding VECTOR(...)`; no es un cambio trivial de configuración.

## Fase 7A.3

`run_booking_graph(BookingConversationState) -> BookingGraphResult` es el contrato interno del graph base. El resultado contiene una copia actualizada del estado, la siguiente `BookingGraphAction`, los campos pendientes, los nodos estructurales visitados y un `response_code` interno. El flujo es determinista y no muta el estado recibido.

Esta fase no incorpora el runtime LangGraph ni tools reales. No consulta PostgreSQL o Redis, no llama a proveedores LLM, no confirma citas o pagos y no genera precios ni disponibilidad. `tenant_id` llega resuelto por backend y `schema_name` no forma parte de la entrada ni del resultado.
