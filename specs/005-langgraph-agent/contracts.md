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

## Fase 7A.4

`ServiceTools` define las tools internas `search_services`, `list_active_services` y `get_service_detail`. Recibe el `tenant_id` ya resuelto por el backend y un repository o sesión SQLAlchemy que ya está contextualizado al schema tenant. Ni las entradas ni los resultados aceptan o exponen `schema_name`.

Las búsquedas devuelven únicamente servicios, profesionales y organizaciones activos. Sus resultados estructurados contienen identificadores internos, nombre, descripción, duración, profesional y modalidades activas. No contienen precio, disponibilidad, slots, citas, pagos ni texto conversacional final. El detalle de un servicio inexistente o inactivo devuelve `None`.

Esta fase no agrega endpoints, llamadas LLM, red, RAG ni runtime LangGraph. El port `ServiceRepository` permite tests locales controlados y `SQLAlchemyServiceRepository` consulta `practitioner_services` como fuente de verdad tenant-scoped.

## Fase 7A.5

`PricingTools` define las tools internas `get_service_price` y `get_pricing_options`. Recibe el `tenant_id` ya resuelto por el backend y un `PricingRepository` o sesión SQLAlchemy contextualizada al schema tenant. Las entradas identifican siempre un servicio del profesional y, para una cotización concreta, un plan de pagador; no aceptan ni exponen `schema_name`.

Los resultados estructurados representan precios configurados y vigentes con la jerarquía `payer_type → payer → payer_plan → practitioner_service_price`, su monto, moneda y periodo de vigencia. Solo se incluyen precio, servicio, plan, pagador, tipo de pagador, profesional, organización y relación organización-profesional activos. Ante periodos activos superpuestos heredados, se selecciona determinísticamente el de `valid_from` más reciente para cada plan.

Esta fase no crea precios ni convierte monedas. Tampoco agrega disponibilidad, slots, citas, pagos, endpoints, llamadas LLM, red o runtime LangGraph. PostgreSQL tenant-scoped continúa como fuente de verdad; COP es la moneda operativa MVP y la tool devuelve la moneda configurada sin alterarla.

## Fase 7A.6

`AvailabilityTools.get_available_slots(AvailabilityRequest) -> AvailabilityToolResult` es la tool interna de consulta de disponibilidad. Recibe `tenant_id` ya resuelto y un `AvailabilityRepository` o una sesión SQLAlchemy ya contextualizada al schema tenant. La solicitud identifica servicio del profesional, profesional, organización, modalidad, rango de fechas y, opcionalmente, sede y consultorio; no acepta ni expone `schema_name`.

`SQLAlchemyAvailabilityRepository` genera slots determinísticos desde reglas recurrentes activas, duración configurada y modalidades activas. Exige servicio, profesional, organización y relación organización-profesional activos; para atención presencial también respeta sedes y consultorios activos. El resultado deduplica slots equivalentes, aplica `slot_limit` y excluye excepciones activas y reservas solapadas en los estados bloqueantes definidos por `InternalSchedulingProvider`.

Los timestamps conservan la representación local sin zona horaria del modelo de agenda existente; la tool no inventa una zona. El resultado es estructurado y no contiene precios, pagos, citas, holds ni texto final. Esta fase es solo lectura: no agrega endpoints, red, LLM, prompts, canales ni integraciones externas.

## Fase 7A.7

`AppointmentTools.create_appointment(AppointmentRequest) -> AppointmentResult` crea una reserva `tentative` que ocupa realmente el horario, y `get_appointment(UUID)` consulta una reserva existente por ID interno. La solicitud recibe paciente y plan ya seleccionados porque el modelo vigente exige sus snapshots, pero el resultado deliberadamente excluye precio y pago.

La creación vuelve a validar el slot con la lógica tenant-scoped de disponibilidad dentro de la misma transacción. Exige servicio, profesional, organización, relación, modalidad y recursos aplicables activos; rechaza excepciones y reservas bloqueantes, y serializa por profesional para impedir carreras de doble ocupación en PostgreSQL. No acepta ni expone `schema_name`, no crea pagos y no agrega endpoints, LLM, red, canales o integraciones externas.

## Fase 7A.8

`PaymentTools.get_payment_status(PaymentStatusRequest) -> PaymentToolResult` consulta el estado financiero de una reserva existente y `prepare_payment(PaymentPreparationRequest) -> PaymentToolResult` crea un intento pendiente para un método expresamente habilitado por la configuración activa de su organización. Sin configuración activa, no se ofrece ningún método.

La transferencia se prepara como `evidence_required`; pago simulado y pago en sitio se preparan como `pending`. Ninguna operación aprueba o rechaza pagos, cambia el estado de la reserva, libera el horario, registra evidencia ni ejecuta expiraciones. Los resultados son instrucciones estructuradas, reciben tenant resuelto, no exponen `schema_name` y no agregan endpoints, LLM, red, Wompi o almacenamiento de archivos.

## Fase 7A.9

`BookingAgent.run(BookingConversationRequest) -> BookingConversationResult` es un coordinador interno determinístico para conversaciones simuladas. Recibe el tenant ya resuelto, busca un servicio y profesional activos, selecciona una tarifa configurada por pagador y plan, consulta disponibilidad, solicita la cita sobre el primer slot retornado y, en un paso separado, prepara únicamente el método de pago solicitado si la configuración lo permite.

El resultado registra los pasos completados y un código estable de desenlace. La creación de cita vuelve a validar el slot mediante `AppointmentTools`; un conflicto detiene el flujo sin preparar pagos. La ausencia de servicio, tarifa o disponibilidad también detiene el flujo conservadoramente. Un método deshabilitado o una reserva no cobrable conserva la cita creada pero no genera intento de pago.

Este contrato no recibe ni expone `schema_name`, no muestra razonamiento, no llama un LLM o la red, no agrega endpoints o canales y no aprueba pagos ni libera cupos. Los UUID del resultado son referencias técnicas internas, no texto conversacional final.

## Fase 8A.6 — realineación contractual grounded

Esta fase es documental; no reemplaza los contratos implementados de 7A ni crea
runtime. El contrato rector es
[`docs/CONVERSATION_ORCHESTRATION.md`](../../docs/CONVERSATION_ORCHESTRATION.md).

El LLM comprende lenguaje natural, identifica intención, mantiene continuidad
con contexto seguro, decide si responde directamente o propone una tool y redacta
la respuesta conversacional normal. El backend resuelve tenant, controla el
catálogo cerrado, valida argumentos tipados, autoriza, aplica reglas y
confirmaciones, revalida hechos, ejecuta tenant-scoped y persiste con transacción,
idempotencia y auditoría. Una solicitud del LLM no autoriza una operación; las
tools son su única frontera para hechos o acciones y devuelven datos estructurados
sin texto conversacional. PostgreSQL sigue siendo la fuente de verdad.

El futuro ciclo contractual será `LLM → ConversationToolRequest → validación
backend → ejecución de tool → ConversationToolResult → respuesta natural LLM`.
Las tools se clasifican en lectura, preparación y mutación. Las mutaciones exigen
estado previo válido, confirmación explícita cuando aplique, idempotency key,
revalidación, transacción, auditoría y concurrencia controlada.

Conceptualmente, `ConversationTurnInput` contiene tenant ya resuelto,
conversación tenant-scoped, texto normalizado, contexto seguro y catálogo
permitido; excluye schema, transporte y secretos. `ConversationToolRequest` es
una propuesta correlacionada con el turno. `ConversationToolResult` separa estado,
resultado estructurado, error seguro, hechos visibles y referencias internas, sin
redactar mensajes. `ConversationTurnResult` contiene texto natural del LLM,
estado permitido, status, auditoría de tool calls y referencias no visibles.

`BookingAgent` 7A.9 se conserva como coordinador operacional determinístico: no
interpreta lenguaje libre, redacta conversación, conoce Telegram ni reemplaza al
LLM. LangGraph podrá coordinar el ciclo futuro sin acceder a schemas, SQL o estado
operacional directamente y sin contener libretos conversacionales.

## Fase 8A.7 — runtime conversacional natural básico

`NaturalConversationRuntime.run(ConversationTurnRequest)` depende exclusivamente
de `LLMProvider`. Construye un prompt pequeño con contexto reciente acotado y
roles permitidos, valida contenido visible no vacío y devuelve contenido, código
estable y metadata técnica mínima. No propaga metadata o razonamiento del
provider. Error, timeout o contenido inválido producen un fallback técnico fijo.

El request contiene tenant y conversación internos ya resueltos, pero esos IDs no
entran al prompt. Tampoco entran schema, credenciales, payloads o identificadores
del transporte. No hay tools, hechos operacionales ni LangGraph completo.

El System Prompt `8a7-v1` materializa reglas rectoras inmutables con una identidad
visible sanitizada y backend-owned. Sus defaults son Sofía/Sofi, género femenino
y MediChat. El usuario puede usar el apodo autorizado, pero sus mensajes no
reconfiguran nombre, tenant, permisos, seguridad o capacidades. La configuración
administrativa y su persistencia quedan fuera de alcance.
