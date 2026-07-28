# Tasks 005 — LangGraph Agent

- [x] Crear LLMProvider.
- [x] Crear OpenAICompatibleProvider multi-proveedor configurable (Fase 7A.1.1).
- [x] Unificar credenciales LLM exclusivamente en `TOTALCHAT_LLM_API_KEY`.
- [x] Crear EmbeddingsProvider.
- [x] Crear semantic_documents.
- [x] Crear graph state (Fase 7A.2: estado interno serializable, sin runtime LangGraph ni persistencia).
- [x] Crear booking graph (Fase 7A.3: flujo estructural determinista, sin tools ni runtime LangGraph).
- [x] Crear tools de servicios (Fase 7A.4: consultas estructuradas tenant-scoped, sin precios ni disponibilidad).
- [x] Crear tools de precios (Fase 7A.5: precios configurados por servicio del profesional y plan, tenant-scoped y sin disponibilidad).
- [x] Crear tools de disponibilidad (Fase 7A.6: slots internos tenant-scoped, sin citas ni holds).
- [x] Crear tools de citas (Fase 7A.7: creación y consulta interna tenant-scoped con ocupación real, sin pagos).
- [x] Crear tools de pagos (Fase 7A.8: consulta y preparación tenant-scoped, sin aprobación ni liberación de cupos).
- [x] Crear tests conversacionales (Fase 7A.9: coordinación determinística de tools, sin LLM ni red).
- [x] Documentar en 8A.6 que el LLM gobierna comprensión, continuidad, decisión
  responder/tool y redacción natural, sin limitarlo a extracción JSON.
- [x] Documentar en 8A.6 la validación backend del catálogo, argumentos, tenant,
  autorización, estado, reglas, confirmaciones, transacciones e idempotencia.
- [x] Documentar en 8A.6 tools de lectura, preparación y mutación y la secuencia
  request → validación → ejecución → resultado → respuesta grounded.
- [x] Conservar `BookingAgent` 7A.9 como coordinador operacional determinístico,
  complementario al LLM y sin responsabilidad de redacción natural.
- [ ] Implementar el runtime LangGraph grounded y sus nodos (fase funcional
  futura expresamente fuera de 8A.6).
- [x] Implementar runtime natural básico sobre `LLMProvider`, contexto seguro y
  fallback técnico, sin tools ni LangGraph completo (Fase 8A.7).
