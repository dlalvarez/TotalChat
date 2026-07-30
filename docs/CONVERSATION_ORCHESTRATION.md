# Orquestación conversacional grounded

## 1. Propósito y estado

Este documento fija el contrato SDD de la **Fase 8A.6 — Realineación SDD del
ciclo conversacional grounded**. La fase es exclusivamente documental y
contractual: no implementa runtime, prompts, nodos, tools ni cambios de canal.

Principio rector:

> El LLM gobierna la experiencia conversacional y la selección de la intención
> o herramienta necesaria. El backend gobierna la autorización, los hechos, las
> reglas de negocio, el estado operacional, las transacciones, la persistencia y
> la ejecución real. Las tools son la única frontera mediante la cual el LLM
> consulta información o solicita acciones.

En forma resumida:

```text
El LLM decide qué necesita.
El backend decide si está permitido.
La tool consulta o ejecuta.
El LLM comunica el resultado naturalmente.
```

Una respuesta es **grounded** cuando se basa exclusivamente en información
explícita del usuario, contexto conversacional permitido, resultados reales de
tools, políticas reales del tenant y hechos persistidos o revalidados por
PostgreSQL.

## 2. Fronteras de responsabilidad

### 2.1. LLM: comprensión y conversación

El LLM comprende mensajes libres, identifica intención, reconoce datos ya
proporcionados, detecta información faltante, resuelve ambigüedades conversando
y mantiene continuidad entre turnos con contexto seguro. Formula preguntas
naturales, guía sin libretos rígidos y decide si responde directamente o propone
una tool. Interpreta resultados estructurados, presenta hechos reales y adapta
tono y redacción al contexto permitido.

Puede responder sin tools a saludos, agradecimientos, despedidas y aclaraciones
que no requieren hechos operacionales. Redacta todas las respuestas
conversacionales normales que recibe el usuario. No se limita a extraer JSON:
una extracción estructurada interna puede ayudar a interpretar, pero no
sustituye su responsabilidad conversacional.

El LLM no autoriza ni ejecuta, no altera estado operacional y no inventa hechos.

### 2.2. Backend: autoridad y ejecución

El backend:

- resuelve el tenant antes de invocar al agente y conserva `schema_name`
  exclusivamente en infraestructura backend;
- prepara y minimiza el contexto seguro;
- expone un catálogo cerrado de tools y valida nombre y argumentos tipados;
- normaliza argumentos y verifica permisos, estado previo, confirmaciones y
  reglas de negocio;
- ejecuta operaciones tenant-scoped, transacciones, idempotencia y control de
  concurrencia;
- revalida hechos susceptibles de cambiar;
- persiste mensajes, estado y auditoría;
- impide mutaciones directas del LLM y afirmaciones sin soporte factual.

El backend determina qué se puede consultar o ejecutar, pero no redacta
normalmente el diálogo.

### 2.3. Tools: frontera operacional única

Las tools exponen capacidades de negocio cerradas, con nombres y propósitos
específicos y argumentos estructurados. Operan con tenant previamente resuelto,
usan repositories y servicios backend, consultan PostgreSQL o providers
autorizados y devuelven resultados estructurados.

No contienen prompts, no llaman al LLM y no redactan frases para el usuario. No
aceptan `schema_name`, credenciales del canal, SQL, HTTP o comandos genéricos; no
exponen UUID como contenido visible. El modelo tampoco puede seleccionar
repositories ni sesiones de base de datos.

Ejemplos de capacidades permitidas:

```text
search_services                 get_service_details
get_pricing_options             get_available_slots
prepare_booking                 confirm_booking
prepare_reschedule              confirm_reschedule
prepare_cancellation            confirm_cancellation
get_payment_options             register_payment_evidence
get_payment_status
```

Estos nombres expresan contratos conceptuales; este documento no crea ni cambia
tools. Quedan prohibidas capacidades abiertas como `execute_sql`, `run_query`,
`call_any_api`, `update_record`, `run_command` y `execute_code`.

### 2.4. Canales: adaptadores de borde

Telegram es el primer adaptador, no el motor conversacional. Los canales reciben,
normalizan, persisten, invocan la frontera común y entregan. Conservan este
contrato:

```text
canal externo
  -> adaptador
  -> tenant resolver
  -> conversación tenant-scoped
  -> agente común
  -> outgoing pending
  -> transporte
  -> sent | failed
```

Un adaptador no interpreta intención, selecciona tools, consulta servicios,
busca disponibilidad, crea citas, procesa pagos ni redacta respuestas normales.
Tampoco decide el tenant desde contenido suministrado por el usuario.
`ConversationAgentInvoker` permanece agnóstico de canales y providers concretos.

### Fase 8A.7 — runtime natural sin tools

`NaturalConversationRuntime` recibe tenant y conversación ya resueltos, texto
normalizado, fase permitida y hasta ocho mensajes recientes. Solo roles
`user`/`assistant`, contenido acotado y fase llegan a `LLMProvider`; IDs, schema,
credenciales, payloads del canal y razonamiento quedan fuera del prompt y del
resultado. El provider redacta íntegramente la respuesta normal. El backend
valida contenido no vacío y usa un fallback técnico genérico ante error o
timeout. En esta fase no existe tool calling ni acceso a datos operacionales.

El System Prompt rector permanece versionado por cada cambio de gobierno. La
identidad visible llega desde un resolver backend-owned separado del prompt
builder. Mientras no exista configuración administrativa persistente, el resolver
usa exclusivamente el fallback técnico neutral `Assistant` / `TotalChat`; no
incorpora nombres de negocio, vertical o tenant en el core. El mensaje del usuario
nunca configura identidad, tenant, permisos o reglas.

El historial contiene solo incoming anteriores y outgoing cuya entrega fue
confirmada como `sent`. Se excluyen `pending`, `failed`, direcciones internas y
la entrada actual antes de aplicar el límite final de ocho mensajes visibles.
La lectura recorre PostgreSQL hacia atrás mediante lotes acotados y cursor
keyset; se detiene al reunir ocho visibles o agotar el historial, sin materializar
la conversación completa ni usar paginación por offset.

Para evitar que reintentos multipliquen la latencia, la configuración backend-owned
usa `max_retries=0` y `max_completion_tokens=256`, con timeout de 30 segundos.
`reasoning_effort` es opcional: si falta, el adaptador omite completamente el
parámetro; `none`, `low`, `medium` o `high` solo se transmiten cuando se configuran
explícitamente y el endpoint los soporta. La validación DeepInfra/Qwen usa
explícitamente `none`, no un default universal. No hay detección de capacidades,
selección dinámica, lógica específica de provider, cambio de modelo, fallback,
tools o LangGraph.

El nombre cercano configurado identifica exclusivamente a la asistente, no al usuario.
Un nombre de usuario solo se usa tras una declaración inequívoca en el contexto
seguro; no existe perfil ni memoria persistente de nombres. Mientras no haya
tools, la identidad resuelta puede comprender, recopilar y organizar una solicitud, pero no puede
prometer consultas, búsquedas, verificaciones, confirmaciones o ejecución futura
de datos operacionales.

### Fase 8A.8 — tool calling de servicios, solo lectura

El runtime expone al provider exclusivamente la definición cerrada
`search_services(query?)`. El modelo puede proponer una llamada; el backend
valida nombre y JSON, rechaza campos adicionales, limita la consulta y la ejecuta
mediante `ServiceTools` sobre la sesión ya contextualizada al tenant. El tenant
no forma parte de los argumentos del modelo.

La búsqueda conversacional y la resolución de selección comparten normalización
de mayúsculas, tildes, tokens genéricos y ranking conservador sobre servicios
activos. La búsqueda informativa puede devolver varias coincidencias seguras para
presentar opciones. La resolución exige un líder inequívoco separado por un
margen mínimo; términos médicos parecidos no se promueven automáticamente.
Ninguna de las dos rutas expone UUIDs. La igualdad normalizada o inclusión
inequívoca sin tokens genéricos puede identificar. Una similitud textual
conservadora solo puede sugerir y nunca confirmar. No se usa stemming casero,
recorte de sufijos ni distancia de edición para identificar términos clínicos.
Un typo o término clínicamente dudoso queda sin resolver y exige aclaración.

La consulta lee servicios activos desde `practitioner_services`. El resultado
que vuelve al modelo contiene únicamente `name`, `description` y
`duration_minutes`; UUID, profesional/organización internos y `schema_name`
quedan fuera. Después de una única consulta permitida, el LLM redacta la
respuesta natural grounded. Tools desconocidas, mutaciones, argumentos inválidos
o más de una llamada producen el fallback técnico controlado y no se ejecutan.

8A.8 no habilita precios, disponibilidad, slots, reservas, pagos, LangGraph,
memoria avanzada ni nuevos canales. Telegram solo activa el mismo invoker común;
no selecciona ni ejecuta tools.

### 2.5. PostgreSQL: fuente de verdad

PostgreSQL es la fuente de verdad operacional para servicios, profesionales,
precios, planes, disponibilidad, reservas, holds, pagos, estados, políticas
persistidas y auditoría. Estado del LLM, LangGraph o conversación no reemplaza
PostgreSQL, confirma hechos ni autoriza operaciones. Los hechos mutables se
revalidan antes de una mutación crítica.

## 3. Ciclo conversacional objetivo

Queda descartado como diseño definitivo:

```text
LLM extrae campos
  -> backend ejecuta if/else
  -> backend construye una frase hardcodeada
  -> canal entrega la frase
```

El ciclo objetivo es:

```text
Usuario
  -> canal
  -> contexto seguro
  -> LLM comprende intención
  -> LLM responde directamente o solicita tool
  -> backend valida solicitud
  -> tool consulta o ejecuta
  -> resultado estructurado
  -> LLM genera respuesta natural grounded
  -> backend persiste
  -> canal entrega
```

### 3.1. Secuencia obligatoria y seguridad de tool calling

1. El LLM propone la tool y argumentos candidatos.
2. El backend verifica que la tool esté registrada en el catálogo permitido.
3. El backend valida y normaliza argumentos con un contrato tipado.
4. El backend verifica tenant y estado previo.
5. El backend aplica autorización, confirmaciones y reglas de negocio.
6. El backend ejecuta la tool mediante servicios autorizados.
7. El backend sanitiza el resultado.
8. El LLM recibe únicamente datos permitidos.
9. El LLM genera la respuesta natural grounded.
10. El backend persiste mensaje y auditoría.

Una solicitud del modelo nunca equivale a autorización. El LLM no llama URLs
directamente, construye SQL, elige schema, inventa tools, cambia el catálogo,
abre sesiones, desactiva confirmaciones ni contradice un resultado de tool para
afirmar otro hecho.

## 4. Clasificación de tools por riesgo

### 4.1. Lectura

Incluyen búsqueda de servicios y consulta de precios, profesionales,
disponibilidad, políticas o estado de cita/pago. Son tenant-scoped, no mutan y
devuelven resultados estructurados. Consultar disponibilidad no reserva ni
protege un recurso.

### 4.2. Preparación

Incluyen preparar reserva, reprogramación, cancelación o método de pago y, solo
cuando una fase futura lo autorice, crear un hold. No ejecutan automáticamente la
acción final. Devuelven resumen, datos faltantes, restricciones y confirmaciones
requeridas.

### 4.3. Mutación

Incluyen confirmar reserva, cancelación o reprogramación; registrar evidencia; y
aprobar o rechazar pagos únicamente si rol y política lo autorizan. Exigen
validación backend, confirmación explícita cuando aplique, idempotency key,
estado previo válido, revalidación de disponibilidad, transacción, auditoría y
control de concurrencia. El LLM nunca las ejecuta mediante acceso HTTP directo.

## 5. Contratos conceptuales (no implementados)

Estos objetos describen la futura frontera interna sin introducir modelos
Pydantic ni dataclasses en 8A.6.

### `ConversationTurnInput`

Representa tenant interno ya resuelto, conversación tenant-scoped, texto
normalizado, contexto seguro y catálogo permitido de tools. No contiene
`schema_name`, token del canal, chat ID, payload externo completo, API keys ni
secretos.

### `ConversationToolRequest`

Representa nombre de tool, argumentos candidatos y correlación con el turno
propuestos por el LLM. Es una propuesta: no constituye autorización ni ejecución.

### `ConversationToolResult`

Representa tool ejecutada, estado, resultado estructurado, error seguro, hechos
visibles permitidos y referencias internas separadas. No incluye mensajes
conversacionales redactados.

### `ConversationTurnResult`

Representa contenido natural generado por el LLM, estado conversacional
permitido, status interno, resumen auditable de tool calls y, cuando sean
necesarias, referencias internas no visibles.

### `ConversationAgentInvoker`

Continúa siendo la frontera de invocación agnóstica de canales y providers
concretos. No recibe detalles de transporte ni secretos.

## 6. Contexto seguro para el LLM

Puede incluir, bajo minimización y aislamiento tenant:

- mensajes recientes relevantes e intención activa;
- datos explícitos proporcionados por el usuario;
- nombres legibles validados y resultados recientes de tools;
- campos pendientes y políticas aplicables;
- nombre visible del tenant;
- tono o personalidad configurada, en una fase futura.

No puede incluir:

- `schema_name`, credenciales, tokens, contraseñas, API keys o URLs con secretos;
- SQL, nombres internos de tablas o payloads completos del canal;
- chain of thought, `reasoning_content` o prompts/material secreto;
- datos de otro tenant;
- información clínica o personal innecesaria.

## 7. Prohibición de libretos normales hardcodeados

Servicios, tools, orquestadores, graphs, adaptadores y handlers no deben contener
textos normales del flujo conversacional destinados al usuario final. Preguntas
como «¿Qué servicio necesitas?», «¿Para qué fecha deseas reservar?» o
«¿Prefieres presencial o virtual?», y presentaciones como «Encontré varias
opciones» o «Los servicios disponibles son», deben generarse por el LLM desde la
intención, el contexto, el siguiente objetivo, los resultados de tools y las
restricciones.

Solo se permiten textos fijos para fallbacks técnicos, indisponibilidad del
provider, errores de seguridad, textos legales exactos, consentimientos
contractuales, alertas críticas o redacción regulatoria obligatoria. Un fallback
técnico nunca sustituye la conversación normal.

## 8. LangGraph y Booking Agent

LangGraph coordinará nodos y transiciones, pero no será fuente de verdad. Un
runtime futuro podrá coordinar:

```text
receive_message -> load_safe_context -> invoke_llm
-> validate_tool_request -> execute_tool -> process_tool_result
-> invoke_llm_for_response -> validate_response -> persist_turn
-> deliver_response
```

La Fase 8A.6 no implementa esos nodos. El grafo no accede directamente a schemas,
se salta domain services, ejecuta SQL, contiene conversación hardcodeada ni
confirma hechos sin tools.

El `BookingAgent` determinístico de 7A.9 se conserva. Coordina reglas y pasos
operativos, reutiliza tools, rechaza estados inválidos, mantiene separados
precio, disponibilidad, cita y pago, y sirve de base determinística para futuras
transiciones. No redacta conversación natural, interpreta lenguaje libre por sí
solo, se comunica con Telegram ni reemplaza al LLM. Ambos son complementarios:
el LLM comprende y conversa; el Booking Agent/backend coordina operación y reglas.

## 9. Continuidad desde 8A.5

8A.5 validó persistencia, entrega y manejo de estado incompleto. Su respuesta
inicial fija fue una implementación transitoria previa al runtime LLM real, no el
diseño textual definitivo y no una fase fallida. Una fase funcional posterior
reemplazará el texto conversacional normal hardcodeado por generación LLM, sin
perder idempotencia, persistencia ni fronteras de canal. 8A.6 no modifica ese
código.

## 10. Secuencia incremental autorizada

- **8A.6 (documental):** esta realineación de responsabilidades y contratos.
- **8A.7 (implementada):** runtime conversacional natural básico, agnóstico de canal
  y sin tools operativas.
- **8A.8 (implementada):** tool calling tenant-scoped de servicios, solo lectura.
- **8A.9 (pendiente):** recolección natural y persistente del contexto inicial de
  reserva.

Precios, disponibilidad, selección de slots, creación de reservas y pagos se
incorporarán incrementalmente solo después de validar servicios y contexto
conversacional. Su numeración y detalle requieren revisar el roadmap vigente y
autorización posterior; no se adelantan en 8A.6.

## 11. Exclusiones de 8A.6

No se implementan código funcional, runtime LangGraph, prompts productivos, tool
calling, tools, canales, disponibilidad conversacional, reservas, holds,
cancelaciones, reprogramaciones, pagos, Wompi, WhatsApp, Redis, RAG, migraciones,
frontend, infraestructura ni correcciones operativas del PR #67.

Cualquier necesidad adicional se registrará como **Desviación propuesta / mejora
futura** y requerirá autorización antes de implementarse.

## 13. Fase 8A.9 — contexto inicial persistente de reserva

El invoker agnóstico de canal conserva un estado conversacional mínimo y
serializable, preparado para convertirse posteriormente en estado de LangGraph:

```text
intent
stage
selected_service (referencia interna y nombre)
candidate_service (mención temporal no confirmada)
collected_context
missing_information
last_relevant_context
conversation_progress (service_confirmed y next_expected_action)
```

La clasificación combina el turno actual con la intención y etapa persistidas.
La interpretación de lenguaje natural pertenece al LLM y produce una propuesta
estructurada (`intent`, `candidate_service` y `service_decision`) sin autoridad
operacional. `service_decision` distingue exploración, selección explícita,
confirmación explícita del candidato previo y ausencia de decisión. El
backend no infiere entidades desde reglas textuales: valida el candidato con la
consulta tenant-scoped antes de modificar `selected_service`.
`booking_request` inicia en `collect_service` con `service` faltante. El turno
siguiente conserva esa intención y resuelve la descripción contra servicios
activos del tenant mediante la capacidad backend existente. Solo igualdad
normalizada o inclusión inequívoca avanza a `service_identified` y persiste su
referencia interna y nombre. Una relación textual conservadora queda como
`suggested_service`, con `service_resolution=suggested`, y permanece en
`collect_service` hasta una confirmación explícita. Sin identificación ni
sugerencia segura, solicita aclaración.
Una solicitud explícita de cambio vuelve a resolver el servicio. Una coincidencia
reemplaza por completo `selected_service`; un cambio sin coincidencia elimina la
selección anterior y regresa a `collect_service`.
`service_information` y `casual_conversation` permanecen en `start` cuando no
existe selección; si ya hay una, conservan `service_identified` sin modificarla.
El LLM recibe una representación segura de este estado y
redacta la pregunta o reconocimiento natural, pero no lo expone al usuario.
Esa representación distingue explícitamente `service_confirmed`,
`service_resolution`, `service_name` validado, `candidate_service` y
`suggested_service_name`. El candidato
es solo una mención: no prueba existencia ni autoriza afirmar que un servicio
está configurado. La respuesta visible solo puede reconocer una entidad cuando
el backend comunica `service_confirmed=true`, `service_resolution=identified` y
el nombre validado, o cuando una consulta `search_services` del mismo turno
devuelve el hecho correspondiente.
`suggested` nunca equivale a `identified`: no selecciona, no confirma existencia
para una reserva y no habilita avance. Una confirmación explícita posterior vuelve
a validar el nombre sugerido tenant-scoped antes de promoverlo. Aliases
persistentes, embeddings y LLM judge quedan como mejoras futuras no implementadas.
La promoción requiere una aceptación afirmativa explícita. Preguntas sobre si el
cambio ya ocurrió —incluidas formas interrogativas como «¿La cambiaste?» o
«¿Ya quedó?»— y aceptaciones ambiguas como «Perfecto» conservan la sugerencia y
deben provocar una nueva solicitud de confirmación, aun si el LLM propone
erróneamente `confirm_candidate`.
Las respuestas de estados críticos son backend-owned y se deciden antes de pedir
redacción al provider: sugerencia pendiente sin selección, candidato `not_found`
y `booking_request` con servicio confirmado usan textos determinísticos. Una
consulta `service_information` conserva redacción natural únicamente cuando
`search_services` devuelve hechos reales; un resultado vacío vuelve al texto
determinístico del candidato. Esto evita perseguir variantes textuales del LLM.

Este contexto es memoria operacional, no fuente de verdad: PostgreSQL valida el
servicio antes de identificarlo. No guarda prompts, razonamiento,
respuestas internas, secretos ni `schema_name`; tampoco habilita disponibilidad,
slots, creación o confirmación de citas, pagos, nuevas tools o un grafo. Telegram
continúa siendo exclusivamente entrada/salida.
El UUID de `selected_service` permanece únicamente en el estado backend. El LLM
recibe solo `service_resolution` y el nombre validado; canales y texto visible no
reciben el UUID.
Una pregunta de existencia o información conserva el candidato como no confirmado
y no selecciona el servicio. Además, el modelo rechaza como inválido cualquier
estado `service_identified` sin `selected_service` confirmado.
Las consultas informativas actualizan `candidate_service` sin reemplazar
`selected_service`. `conversation_progress` deriva exclusivamente del estado
confirmado: indica `continue_booking` cuando existe servicio seleccionado o
`collect_service` cuando falta. Es una orientación no transaccional y nunca
implica que exista una reserva, disponibilidad o próxima operación habilitada.
8A.9 tampoco recolecta fecha, hora, preferencias de horario, sede ni datos
personales, y no promete consultar disponibilidad, separar o crear una cita. El
runtime aplica una protección cerrada para sustituir una salida del provider que
contradiga estas fronteras por una aclaración segura basada en el estado backend.
La protección recibe también la intención actual. En `service_information`, una
consulta sobre otro candidato se responde con el resultado de `search_services`
—o con la ausencia de resultados— sin reemplazar ni convertir en tema exclusivo
el `selected_service` previo. `not_found` siempre describe el candidato del turno
y tiene prioridad sobre cualquier reconocimiento de una selección anterior.
Una exploración nunca modifica entidades confirmadas. Solo `select` o
`confirm_candidate`, propuestos por interpretación LLM y validados por el backend,
pueden crear o reemplazar `selected_service`. Una respuesta ambigua conserva el
candidato sin promoverlo. Esta regla constituye el patrón reusable futuro para
profesional, sede, pagador, plan y slot, que permanecen fuera de esta fase.
