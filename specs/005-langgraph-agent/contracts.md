# Contracts — 005-langgraph-agent

Pendiente de definir endpoints/API contracts durante el plan técnico.


## Fase 7A.1

No se agregan endpoints HTTP ni contratos de canal. Los contratos internos nuevos son `LLMProvider`, `EmbeddingsProvider` y `OpenAIProvider`, todos bajo tenant ya resuelto por backend para usos futuros.

## Fase 7A.1.1

`OpenAICompatibleProvider` implementa los contratos internos para OpenAI y DeepInfra/Qwen mediante configuración genérica. Devuelve `LLMResponse(content, model, provider)` solo desde `choices[0].message.content` y descarta `reasoning_content`. La factory selecciona provider antes de cualquier LangGraph futuro. No se agregan endpoints HTTP, fallback automático, configuración por tenant ni exposición de `schema_name`.
