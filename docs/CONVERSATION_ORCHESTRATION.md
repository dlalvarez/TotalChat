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

El System Prompt rector está versionado como `8a7-v1`. La identidad visible
backend-owned usa por defecto a **Sofía** (nombre cercano **Sofi**), identidad
femenina y vertical MediChat, y puede inyectarse de forma segura por contexto
conversacional. El mensaje del usuario nunca configura identidad, tenant,
permisos o reglas. No existe todavía configuración administrativa persistente.

El historial contiene solo incoming anteriores y outgoing cuya entrega fue
confirmada como `sent`. Se excluyen `pending`, `failed`, direcciones internas y
la entrada actual antes de aplicar el límite final de ocho mensajes visibles.

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
- **8A.7 (pendiente):** runtime conversacional natural básico, agnóstico de canal
  y sin tools operativas.
- **8A.8 (pendiente):** tool calling tenant-scoped de servicios, solo lectura.
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
