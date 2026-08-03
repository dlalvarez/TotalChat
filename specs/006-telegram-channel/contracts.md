# Contracts — 006-telegram-channel

## Fase 8A.1 — Entrada

`POST /api/webhooks/telegram/{webhook_secret}` compara el secreto con
`TOTALCHAT_TELEGRAM_WEBHOOK_SECRET`. El backend resuelve el canal activo mediante
`TOTALCHAT_TELEGRAM_BOT_IDENTIFIER`; el payload y el LLM nunca seleccionan tenant
ni schema. `TOTALCHAT_TELEGRAM_BOT_TOKEN` queda configurado por entorno para una
fase saliente posterior y no se usa en 8A.1.

La entrada soporta `update_id` y un mensaje de texto con `message_id`, `chat.id` y
`text`. Un canal sin tenant activo recibe `200 {"ok": true}` sin escritura tenant;
un secreto inválido recibe `404`. Para un canal válido, se crea o reutiliza una
sesión tenant-scoped y se persiste el mensaje `incoming`. `update_id` es el
identificador idempotente. Solo se guardan identificadores técnicos mínimos, sin
secretos, perfil de usuario ni `schema_name`.

Exclusiones: Booking Agent/LLM, red, cliente Telegram, mensajes salientes,
comandos y lógica de reservas o pagos.

## Fase 8A.2 — Puente interno al Booking Agent

Después de persistir y confirmar el mensaje `incoming`, el servicio construye una
`BookingConversationRequest` con una lista cerrada de campos del estado de la
sesión tenant-scoped y el texto recibido como consulta de servicio. El `tenant_id`
proviene exclusivamente del resolver de canal. El puente instancia las tools SQL
tenant-scoped y ejecuta el `BookingAgent` determinístico de 7A.9.

El resultado se guarda como un `Message(direction="outgoing")` interno con
`delivery_status="pending"`. Este estado significa generado pero **no enviado**.
Los errores controlados también dejan una respuesta interna genérica pendiente y
no cambian el `200` del webhook; no se persisten detalles de excepción. Un update
duplicado no vuelve a invocar el agente.

Exclusiones: cliente o API saliente de Telegram, red, LLM/provider, LangGraph
runtime y cualquier estado `sent` o confirmación de entrega.

## Fase 8A.3 — Entrega saliente controlada

Después de persistir el mensaje `outgoing` con estado `pending`, el backend usa
el token configurado por entorno para llamar `sendMessage`. Solo una confirmación
válida de Telegram cambia el estado a `sent`; una excepción de red o respuesta no
confirmada cambia el estado a `failed` sin alterar la respuesta exitosa del
webhook. Un update ya procesado no vuelve a invocar el agente ni a entregar el
mensaje. El token, `schema_name` y los detalles de excepciones no se persisten ni
se incluyen en respuestas.

Exclusiones: reintentos, jobs, colas, LLM, LangGraph runtime y otros canales.

## Fase 8A.4 — Contrato común de canales

Telegram es el primer adaptador concreto de un flujo conversacional propiedad del
backend; no es el modelo del core. Cada adaptador futuro deberá traducir su
payload externo a los conceptos internos existentes (`channel_type`, sesión de
conversación, mensaje, `direction` y estado de entrega) y conservar sus campos,
credenciales y confirmaciones de transporte dentro del límite del adaptador.

El límite común de invocación al agente es `ConversationAgentInvoker`: recibe
exclusivamente el `tenant_id` ya resuelto por el backend, la conversación
tenant-scoped y el texto normalizado. No recibe payloads, tokens, chat IDs,
`schema_name` ni tipos de Telegram. El adaptador es responsable de la entrada,
la idempotencia del identificador externo y la traducción de la confirmación de
entrega a `pending`, `sent` o `failed`; el agente no conoce esos detalles.

Flujo obligatorio:

```text
canal externo
  -> adaptador concreto
  -> resolución backend de tenant
  -> conversación/mensaje tenant-scoped
  -> ConversationAgentInvoker
  -> mensaje outgoing pending
  -> transporte del adaptador
  -> sent | failed
```

Un canal futuro debe implementar estas fronteras sin copiar reservas, precios,
disponibilidad, pagos ni selección de tenant al adaptador. Esta fase no agrega
canales, endpoints, runtime LLM/LangGraph, colas, jobs ni reintentos y no modifica
el flujo observable de Telegram 8A.1–8A.3.

## Fase 8A.5 — Respuesta inicial con contexto incompleto

Cuando `conversation_sessions.state` no contiene el contexto mínimo requerido
por el agente determinístico, el backend no lo invoca ni expone su fallback
técnico. Actualiza el estado tenant-scoped con la fase
`collecting_booking_context`, el último texto recibido y la lista de campos
faltantes, y genera una respuesta conversacional que solicita el servicio.

El estado previo permitido se conserva y la respuesta se persiste y entrega con
la semántica `pending` → `sent | failed` existente. Ni el estado ni el texto
visible incluyen `schema_name`, UUIDs, precios, disponibilidad o citas inventadas.
Esta fase no interpreta intención ni completa el flujo natural de reserva.

## Fase 8A.6 — frontera conversacional grounded (documental)

8A.5 permanece válida como implementación transitoria: probó estado incompleto,
persistencia y entrega, pero su texto fijo no es el diseño conversacional
definitivo. 8A.6 no modifica ese código. Una fase posterior reemplazará la
redacción normal hardcodeada por generación LLM y conservará idempotencia,
persistencia y la semántica `pending → sent | failed`.

Telegram continúa siendo solo el primer adaptador. Recibe, normaliza, persiste,
invoca `ConversationAgentInvoker` y entrega; no interpreta intención, selecciona
tools, consulta dominio, crea reservas o pagos, redacta diálogo ni resuelve tenant
desde texto del usuario. `ConversationAgentInvoker` sigue agnóstico del canal y
provider concreto.

El futuro input conceptual del agente recibe tenant interno ya resuelto,
conversación tenant-scoped, texto normalizado, contexto seguro y catálogo de
tools. No recibe payload externo completo, chat ID, token, `schema_name`, API keys
o secretos. La salida conversacional natural pertenece al LLM; tools y backend
solo retornan resultados estructurados o fallbacks técnicos controlados.

El contrato detallado, incluida la prohibición de libretos normales y la
secuencia de tool calling, está en
[`docs/CONVERSATION_ORCHESTRATION.md`](../../docs/CONVERSATION_ORCHESTRATION.md).
Esta fase no introduce runtime, modelos, prompts, tools, endpoints ni cambios de
Telegram.

## Fase 8A.7 — runtime conversacional natural básico

Telegram invoca siempre `ConversationAgentInvoker` después de hacer durable el
incoming. Su implementación natural carga historial reciente tenant-scoped,
invoca el runtime basado en `LLMProvider` y devuelve el texto visible completo.
El adaptador lo persiste sin reescritura como `outgoing/pending` y conserva la
entrega `sent | failed`. Un update duplicado termina antes de invocar o entregar.

La respuesta fija normal de 8A.5 deja de ser una ruta de ejecución. Solo se
permite el fallback técnico genérico ante fallos o contenido inválido. Telegram
no contiene prompts ni configuración LLM y al runtime no llegan token, chat ID,
payload completo o schema. Esta fase no conecta tools ni datos operacionales.

El historial del invoker se forma exclusivamente con incoming anteriores y
outgoing confirmados `sent`; `pending`, `failed`, direcciones desconocidas y la
entrada actual quedan fuera. El límite de ocho se aplica después de ese filtro.
La identidad externa y el fallback técnico neutral son responsabilidad del
resolver backend-owned, nunca configuración de Telegram ni del prompt builder.
El invoker obtiene ese historial mediante lectura descendente en lotes limitados
y keyset `(created_at, id)`, deteniéndose al reunir ocho visibles o agotar el
historial. No carga toda la conversación ni usa `OFFSET`.

## Fase 8A.8 — tool calling tenant-scoped de servicios

El invoker común habilita el catálogo cerrado con una única tool de lectura:
`search_services({query?})`. La sesión ya seleccionada por el resolver constituye
el contexto tenant; tenant y `schema_name` nunca son argumentos del LLM. El
backend valida la solicitud, consulta `practitioner_services` mediante la capa de
servicios existente y entrega al LLM únicamente nombre, descripción y duración.
El LLM genera la respuesta visible final.

La consulta informativa usa el mismo ranking normalizado y conservador que la
resolución conversacional. Puede devolver múltiples opciones; no elige una. La
resolución solo confirma una coincidencia única con margen seguro y rechaza
términos médicos meramente parecidos. UUIDs y puntajes permanecen internos.
La política clínica permite identificar solo por igualdad normalizada o inclusión
inequívoca sin tokens genéricos. La similitud textual conservadora puede producir
una sugerencia, nunca una selección. No se usa stemming, recorte de sufijos ni
distancia de edición para identificar. Un typo dudoso permanece sin resolver.

Telegram no conoce el catálogo, los argumentos ni los resultados. Continúa
limitándose a persistencia, invocación y entrega. No se habilitan precios,
disponibilidad, reservas, pagos ni otras tools.

## Fase 8A.9 — contexto conversacional inicial de reservas

El invoker común clasifica cada turno dentro del vocabulario cerrado
`booking_request | service_information | casual_conversation`, combinando el
mensaje con el estado tenant-scoped ya persistido. El estado JSON permitido
contiene solo `intent`, `stage`, `collected_context`, `missing_information` y
`last_relevant_context`, más `selected_service` como referencia backend tipada
con UUID y nombre, `candidate_service` como propuesta temporal sin UUID y
`suggested_service` como servicio real relacionado sin ID visible. Una
solicitud de cita avanza a `collect_service`. La
descripción del turno siguiente se normaliza y resuelve contra los servicios
activos del tenant mediante la consulta backend existente; solo una coincidencia
inequívoca avanza a `service_identified` con ID interno y nombre. Una similitud
conservadora persiste `service_resolution=suggested` y mantiene `collect_service`
hasta confirmación explícita. Sin coincidencia se solicita aclaración. Esta es una corrección del
contrato de 8A.9, no una fase nueva.

Una petición explícita de cambio de servicio se resuelve nuevamente. Si existe
una coincidencia única reemplaza la selección; si no existe, elimina la selección
anterior y vuelve a `collect_service`. El UUID nunca se incorpora al contexto del
LLM, al texto visible ni al payload de Telegram; el runtime recibe únicamente el
estado de resolución y el nombre validado.

La interpretación LLM produce exclusivamente una propuesta estructurada de
intención, candidato y decisión (`none | explore | select | confirm_candidate |
confirm_pending_suggestion | reject_pending_suggestion`).
Una pregunta informativa puede conservar candidato, pero
no crea `selected_service`. Solo el resolver backend tenant-scoped promueve un
candidato de reserva a selección confirmada. El modelo rechaza
`service_identified` cuando no existe `selected_service`.
Una consulta informativa reemplaza únicamente `candidate_service` y conserva la
selección confirmada previa. `conversation_progress` refleja de manera derivada
si el servicio está confirmado y orienta a `continue_booking` o
`collect_service`; no representa reserva, agenda ni acción ejecutable.
`select` opera sobre un candidato nombrado. `confirm_pending_suggestion` puede
promover únicamente `current.suggested_service` después de resolver nuevamente su
nombre tenant-scoped; nunca usa una entidad inventada por el LLM.
`reject_pending_suggestion` limpia la sugerencia y conserva la selección previa.
`explore`, `none` y confirmaciones ambiguas preservan `selected_service`.

El estado se entrega al runtime como contexto seguro para que el LLM solicite la
información faltante naturalmente. No se muestra al usuario ni contiene prompts,
razonamiento, respuestas internas, secretos o `schema_name`. La coincidencia solo
valida un servicio activo; no consulta disponibilidad, crea citas, bloquea horarios o
procesa pagos. Telegram continúa limitado a entrada, persistencia, invocación y
entrega; no clasifica ni conduce el flujo.

El contexto seguro diferencia `service_confirmed`, `service_resolution`, el
`service_name` validado y el `candidate_service` temporal. Un candidato nunca
confirma existencia. Solo `service_confirmed=true` junto con
`service_resolution=identified` y `service_name`, o un resultado real de
`search_services` en ese turno, permite comunicar que el servicio existe. El
runtime rechaza respuestas visibles que contradigan esa autoridad o que soliciten
fecha, hora, disponibilidad o datos de agenda, y tampoco permite prometer o crear
una reserva en 8A.9.
El guard distingue `service_information` de una solicitud de reserva: una
consulta informativa se orienta al `candidate_service` y al resultado de
`search_services`, mientras preserva el `selected_service`. Una resolución
`not_found` prioriza el candidato actual y nunca cae en un reconocimiento de la
selección previa ni sugiere continuar con la entidad inexistente.
`suggested` no equivale a `identified`, no confirma selección ni reserva y no
habilita el siguiente paso. Su nombre seguro puede mostrarse para preguntar si el
usuario se refiere a ese servicio; una confirmación explícita posterior debe
resolver nuevamente el nombre real antes de promoverlo. Aliases persistentes,
embeddings y LLM judge quedan fuera de 8A.9.
La confirmación se interpreta semánticamente como `confirm_pending_suggestion`, no
mediante una lista sintáctica de frases. El backend exige que exista sugerencia,
que el turno no sea interrogativo ni informativo y que no proponga otro candidato;
luego vuelve a resolver el nombre persistido. Una pregunta sobre si el cambio
ocurrió y expresiones sociales o ambiguas no promueven la sugerencia.
El runtime decide antes de invocar al provider las respuestas para
`suggested_service` pendiente, `not_found` y solicitudes de reserva con selección
confirmada. Solo una consulta informativa respaldada por resultados no vacíos de
`search_services` conserva redacción LLM; la ausencia de resultados usa respuesta
determinística. Estos textos no contienen UUID, tenant, `schema_name` ni prompts.
Cuando `selected_service` y una `suggested_service` diferente coexisten, la primera
permanece confirmada y la segunda representa un cambio pendiente. Una intención de
cambio o seguimiento ambiguo produce una respuesta determinística que prioriza la
sugerencia y solicita confirmación; solo después se reemplaza la selección.
