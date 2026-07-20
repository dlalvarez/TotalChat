# AI_BOUNDARIES.md  
# Límites de IA en TotalChat

## 1. Principio central

La IA conversa y orquesta, pero no es la fuente de verdad.

## 2. Permitido

La IA puede:

- Entender intención.
- Pedir datos faltantes.
- Resolver ambigüedad.
- Presentar servicios.
- Presentar horarios retornados por herramientas.
- Explicar opciones de pago.
- Guiar paso a paso.
- Redactar mensajes naturales.
- Interpretar respuestas de recordatorios.
- Prevalidar comprobantes de pago.
- Buscar semánticamente servicios y políticas.

## 3. Prohibido

La IA no puede:

- Inventar precios.
- Inventar horarios.
- Confirmar pagos sin herramienta.
- Confirmar citas sin herramienta.
- Inventar links virtuales.
- Diagnosticar.
- Elegir tenant/schema.
- Aprobar transferencias.
- Crear reembolsos no autorizados.
- Modificar reglas del tenant por conversación.
- Saltarse políticas configuradas.

## 4. Herramientas controladas

El agente debe usar herramientas como:

- search_services.
- get_pricing_options.
- get_available_slots.
- create_tentative_booking.
- confirm_booking.
- create_payment_attempt.
- register_payment_evidence.
- get_payment_status.
- cancel_booking.
- reschedule_booking.

## 5. LLMProvider

Debe existir abstracción:

```text
LLMProvider
OpenAICompatibleProvider
OpenAIProvider
```

Futuro:

```text
OllamaProvider
```

## 6. Proveedores OpenAI-compatible

OpenAI y DeepInfra/Qwen se configuran detrás de `OpenAICompatibleProvider`. LangGraph, Conversation Engine, canales, tools y dominio solo dependen de `LLMProvider`/`EmbeddingsProvider`: nunca llaman SDKs, endpoints ni contratos de OpenAI, DeepInfra, Kimi u otros directamente. No existe fallback automático ni selección por tenant en esta fase.

`TOTALCHAT_LLM_API_KEY` es la única credencial LLM aceptada para OpenAI, DeepInfra/Qwen, Kimi futuro y cualquier proveedor OpenAI-compatible. No existe compatibilidad ni fallback hacia variables específicas de proveedor.

LLM y embeddings pueden usar proveedores distintos. El ejemplo MVP combina LLM DeepInfra/Qwen con embeddings OpenAI `text-embedding-3-small` de 1536 dimensiones. Antes de cambiar embeddings a DeepInfra/Qwen Embedding se debe validar la dimensión real: el vector persistido y `TOTALCHAT_EMBEDDING_DIMENSIONS` deben coincidir, y cambiar esa dimensión no es una simple sustitución de configuración.

El backend resuelve provider, URL, credencial y modelo. El LLM no resuelve tenant ni schema, y `schema_name` no entra en prompts o respuestas. Solo `message.content` es visible. `reasoning_content` es metadata técnica opcional: no se muestra a usuarios finales, frontend o canales, y no se guarda ni registra por defecto. Puede capturarse exclusivamente en `LLMResponse.metadata` con `TOTALCHAT_LLM_CAPTURE_REASONING=true` para diagnóstico técnico y tuning de prompts, sin persistencia en esta fase. Ninguna lógica de negocio, tool, pago, cita, disponibilidad, autorización o tenant puede depender de ella. Las API keys no se registran y cualquier key expuesta en una conversación debe rotarse.

## 7. Comprobantes de pago

La IA puede extraer información de comprobantes, pero debe marcar su resultado como prevalidación.

Resultado posible:

```text
Monto coincide
Cuenta parece coincidir
Fecha parece válida
Referencia detectada
Requiere revisión humana
```

Nunca:

```text
Pago confirmado
```

## 8. Emergencias médicas

Si el usuario describe una emergencia, el agente debe recomendar atención inmediata.

No debe diagnosticar.

## 9. pgvector

pgvector apoya búsqueda semántica.

No reemplaza lógica transaccional.

## 10. Auditoría de herramientas

Se deben registrar:

- Intención detectada.
- Herramientas llamadas.
- Resultado resumido.
- Errores.
- Estado conversacional.


## 11. Fase 7A.1 — providers y documentos semánticos

La primera entrega de Fase 7 define providers testeables sin red y `semantic_documents` tenant-scoped. El `OpenAIProvider` solo puede usarse después de configuración explícita y no se invoca en tests. Los embeddings preparan almacenamiento para recuperación futura, pero no autorizan al modelo a inventar precios, disponibilidad, pagos, citas ni políticas.

La Fase 7A.1.1 tampoco agrega LangGraph, tools, endpoints HTTP ni resolución de tenant por IA. Añade exclusivamente configuración genérica y el adaptador OpenAI-compatible para OpenAI y DeepInfra/Qwen.
