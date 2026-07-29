# AI_BOUNDARIES.md  
# Límites de IA en TotalChat

## 1. Principio central

La IA conversa y orquesta, pero no es la fuente de verdad.

El contrato completo del ciclo grounded está en
[`CONVERSATION_ORCHESTRATION.md`](CONVERSATION_ORCHESTRATION.md). En síntesis: el
LLM decide qué necesita; el backend decide si está permitido; la tool consulta o
ejecuta; y el LLM comunica el resultado naturalmente.

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

La primera entrega de Fase 7 define providers testeables sin red y `semantic_documents` tenant-scoped. OpenAI, DeepInfra/Qwen y Kimi futuro son configuraciones de `OpenAICompatibleProvider`, no adaptadores separados. Los consumidores deben usar `LLMProvider`/`EmbeddingsProvider` y factories internas. Los embeddings preparan almacenamiento para recuperación futura, pero no autorizan al modelo a inventar precios, disponibilidad, pagos, citas ni políticas.

La Fase 7A.1.1 tampoco agrega LangGraph, tools, endpoints HTTP ni resolución de tenant por IA. Añade exclusivamente configuración genérica y el adaptador OpenAI-compatible para OpenAI y DeepInfra/Qwen.

## 12. Fase 7A.2 — estado conversacional base

El estado del futuro Booking Agent recibe `tenant_id` después de que el backend haya resuelto el tenant. Es estado temporal de coordinación: sus referencias y estados críticos deben contrastarse con PostgreSQL mediante tools y servicios de dominio futuros antes de actuar.

Su representación serializable excluye `schema_name`, `reasoning_content`, credenciales y prompts. La metadata se valida para impedir que esos datos entren indirectamente. La Fase 7A.2 no incluye Redis, LangGraph runtime, tools, llamadas LLM, endpoints ni canales.

## 13. Fase 7A.3 — booking graph base

El booking graph base clasifica de forma determinista la siguiente etapa, detecta campos básicos faltantes y devuelve una acción interna estructurada. Opera sobre una copia de `BookingConversationState`; no ejecuta dominio ni convierte las referencias del estado en hechos confirmados.

Las acciones `review_booking`, `handle_payment` y `complete` describen únicamente el siguiente paso de coordinación. No confirman una cita o un pago. Esta fase no usa tools, PostgreSQL, Redis, red, LLM, prompts, endpoints ni canales, y nunca recibe `schema_name`.

## 14. Fase 7A.4 — tools de servicios

Las tools de servicios reciben un tenant ya resuelto y consultan servicios del profesional mediante un repository o sesión tenant-scoped. Solo devuelven datos estructurados de servicios activos; no aceptan ni exponen `schema_name` y no seleccionan tenant.

Estas tools no llaman al LLM ni a la red, y separan estrictamente servicios de precios, disponibilidad, citas y pagos. Los IDs devueltos son referencias internas para el backend, no texto final para el usuario.

## 15. Fase 7A.5 — tools de precios

Las tools de precios consultan PostgreSQL mediante un repository o sesión tenant-scoped y reciben el tenant ya resuelto. Solo presentan precios activos y vigentes definidos por `practitioner_service + payer_plan`, junto con la información mínima de tipo de pagador, pagador y plan; nunca inventan un precio genérico ni aceptan o exponen `schema_name`.

Esta fase no consulta disponibilidad, genera slots, crea citas o pagos, convierte moneda ni llama a LLM, red, endpoints o canales. Los estados activos del servicio, plan, pagador, tipo de pagador, profesional, organización y su relación se validan antes de exponer una cotización.

## 16. Fase 7A.6 — tools de disponibilidad

Las tools de disponibilidad reciben el tenant resuelto por backend y leen reglas recurrentes, modalidades, excepciones y ocupación desde PostgreSQL tenant-scoped. Devuelven slots estructurados y determinísticos solo cuando servicio, profesional, organización, relación, sede y consultorio aplicables continúan activos; nunca aceptan ni exponen `schema_name`.

Consultar disponibilidad no reserva ni protege el horario. Esta fase no crea citas u holds, no mezcla precios o pagos y no usa LLM, prompts, red, endpoints, canales ni integraciones externas. Como el modelo actual guarda horarios de reglas sin zona asociada, la tool conserva de forma explícita esos valores como hora local del tenant y no inventa una zona horaria.

## 17. Fase 7A.7 — tools de citas

Las tools de citas reciben el tenant resuelto y crean una reserva tentativa únicamente después de revalidar la disponibilidad real en PostgreSQL. La reserva constituye ocupación real; se rechazan recursos inactivos, modalidades o lugares no aplicables, excepciones y cualquier reserva bloqueante solapada.

El resultado estructurado no expone precio, pago ni `schema_name`. El plan seleccionado solo se usa internamente para completar los snapshots obligatorios del modelo vigente: esta fase no crea, aprueba ni modifica pagos, y tampoco llama LLM, red, endpoints o canales.

## 18. Fase 7A.8 — tools de pagos

Las tools de pagos consultan reservas e intentos desde PostgreSQL tenant-scoped y solo ofrecen métodos habilitados en la configuración activa de la organización. La ausencia de configuración produce el resultado conservador de ningún método disponible. Transferencia requiere evidencia y revisión humana; los demás métodos se preparan pendientes.

Estas tools nunca aprueban o rechazan un pago, registran evidencia, cambian o liberan una reserva, recalculan disponibilidad ni llaman LLM, red, endpoints, canales o pasarelas. El tenant llega resuelto por backend y `schema_name` no forma parte de entradas o resultados.

## 19. Fase 7A.9 — conversaciones simuladas determinísticas

El coordinador interno del Booking Agent encadena las tools existentes en el orden servicio, precio, disponibilidad, cita y pago. La selección se basa únicamente en resultados estructurados: no inventa alternativas y la cita revalida el slot antes de ocuparlo. Preparar el pago es un paso posterior e independiente de crear la cita.

Esta simulación no interpreta lenguaje con IA, no llama providers LLM ni usa red. Tampoco aprueba pagos, libera cupos, ejecuta expiraciones o convierte al estado conversacional en fuente de verdad. El tenant continúa resuelto por backend y `schema_name` queda fuera de solicitudes y resultados.

## Entrada Telegram — Fase 8A.1

La entrada termina después de que el backend resuelve el tenant desde
`tenant_channels` y persiste el mensaje entrante. No importa ni invoca providers
LLM, LangGraph runtime o `BookingAgent`; tampoco entrega el payload a IA, realiza
llamadas de red o envía mensajes. El LLM no participa en la selección de tenant o
schema, y `schema_name` no cruza la frontera del backend.

## Puente Telegram al agente — Fase 8A.2

El backend invoca el `BookingAgent` determinístico solo después de resolver el
tenant y hacer durable el mensaje entrante. La request interna se construye con
campos permitidos del estado tenant-scoped; el texto entrante se usa como consulta
de servicio, nunca para seleccionar tenant o schema. El resultado o un error
controlado se persiste como mensaje saliente `pending`, sin LLM, red ni entrega a
Telegram. El estado `outgoing` en esta fase no acredita un envío.

## Entrega Telegram — Fase 8A.3

La entrega saliente consume únicamente el texto ya generado y persistido por el
puente determinístico. No invoca un LLM, no modifica el contrato del agente y no
inventa contenido. El cliente Telegram recibe el token solo desde configuración;
ni el token ni `schema_name` forman parte del mensaje o del estado de entrega.

## Contrato común de canales — Fase 8A.4

El agente se encuentra detrás de `ConversationAgentInvoker`, un límite interno
agnóstico del proveedor. El adaptador concreto normaliza el texto y el backend
aporta el `tenant_id` ya resuelto y la conversación tenant-scoped. Payloads,
credenciales, identificadores de chat, `schema_name` y resultados propios del
transporte no cruzan hacia el agente.

El agente genera contenido interno, pero no recibe webhooks ni entrega mensajes;
el adaptador entrega únicamente un `outgoing` ya persistido. Un canal futuro debe
reutilizar este límite y las tools backend existentes, no copiar decisiones de
tenant, disponibilidad, reservas, pricing o pagos. Esta fase no incorpora nuevos
canales, LLM ni runtime LangGraph.

## Fase 8A.6 — responsabilidad conversacional grounded

### Implementación 8A.7 sin tools

El runtime básico depende solo de `LLMProvider` y permite al modelo redactar
conversación social e intención inicial con contexto reciente acotado. No ofrece
tools ni hechos operacionales. Su resultado conserva contenido, código estable y
metadata mínima, pero descarta metadata y razonamiento del provider. Errores y
contenido vacío se convierten en un fallback técnico genérico.

El prompt rector `8a7-v2` separa reglas inmutables de identidad visible. La
identidad backend-owned predeterminada es Sofía/Sofi, femenina y MediChat; una
identidad alternativa solo puede inyectarse desde composición backend tras
sanitización, nunca desde texto del usuario. No contiene tenant IDs, UUIDs ni
schemas configurados. Solo mensajes realmente visibles —incoming previos y
outgoing `sent`— regresan al LLM; `pending` y `failed` se excluyen.

Los controles operativos del adaptador son backend-owned. `reasoning_effort` es
opcional: ausente no se envía; `none` se envía explícitamente para deshabilitar
reasoning solo cuando el endpoint configurado lo soporte, y `low`, `medium` o
`high` también requieren soporte declarado por ese endpoint. TotalChat no detecta
capacidades automáticamente. Los reintentos quedan por defecto en cero para no
multiplicar el timeout de 30 segundos y las completions se limitan a 256 tokens.
8A.7 no selecciona esfuerzo dinámicamente, cambia provider/modelo, implementa
fallback entre providers ni habilita tools.

El nombre cercano configurado pertenece a la asistente y no se infiere como
nombre del usuario; solo una declaración inequívoca del propio usuario dentro del
contexto seguro permite dirigirse a él por un nombre. Sin tools, el runtime puede
comprender, recopilar y organizar solicitudes, pero no promete consultar, buscar,
verificar o confirmar posteriormente información u operaciones.

El LLM no es solo un extractor estructurado: comprende lenguaje libre, identifica
intención, usa contexto seguro, resuelve ambigüedades, decide si responde o
propone una tool e interpreta sus resultados. Genera todas las respuestas
conversacionales normales, grounded exclusivamente en datos del usuario,
contexto permitido, resultados reales de tools, políticas reales y hechos de
PostgreSQL.

El backend conserva autoridad sobre tenant, autorización, catálogo, argumentos,
reglas, confirmaciones, estado, transacciones, concurrencia, persistencia,
idempotencia y auditoría. Una tool request es solo una propuesta. Las tools son
capacidades cerradas tenant-scoped, no aceptan schema o secretos y devuelven
resultados estructurados sin redactar conversación.

Servicios, tools, orquestadores, graphs, adaptadores y handlers no pueden alojar
libretos normales para el usuario final. Solo se permiten fallbacks técnicos,
errores de seguridad, alertas críticas y textos legales, contractuales o
regulatorios exactos; nunca como sustituto del diálogo normal. La clasificación
de tools por lectura, preparación y mutación, la secuencia de validación y el
contexto seguro se especifican en el contrato rector enlazado arriba.
