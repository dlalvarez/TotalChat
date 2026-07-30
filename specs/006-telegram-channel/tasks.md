# Tasks 006 — Telegram

- [x] Crear endpoint webhook de entrada (Fase 8A.1).
- [x] Configurar token/secreto mediante variables de entorno, sin uso de red (Fase 8A.1).
- [x] Resolver tenant desde el canal Telegram activo configurado en backend (Fase 8A.1).
- [x] Persistir incoming messages con tolerancia a updates repetidos (Fase 8A.1).
- [x] Invocar agente y persistir su resultado interno pendiente (Fase 8A.2).
- [x] Enviar respuesta `outgoing pending` y persistir su resultado (Fase 8A.3).
- [x] Probar flujo básico de entrada, sin agente ni respuesta saliente (Fase 8A.1).
- [x] Extraer el contrato agnóstico de invocación del agente fuera del adaptador Telegram (Fase 8A.4).
- [x] Documentar fronteras de entrada, persistencia, agente y entrega para canales futuros (Fase 8A.4).
- [x] Verificar que el contrato común no expone `schema_name` ni depende de adaptadores futuros (Fase 8A.4).
- [x] Detectar estado vacío o incompleto antes de invocar el agente determinístico (Fase 8A.5).
- [x] Persistir fase, último mensaje y campos faltantes, y responder de forma conversacional (Fase 8A.5).
- [x] Cubrir estados vacío e incompleto sin adelantar interpretación o reserva natural (Fase 8A.5).
- [x] Realinear documentalmente el ciclo conversacional grounded y las fronteras
  de LLM, backend, tools, canales y PostgreSQL (Fase 8A.6, sin código funcional).
- [x] Documentar 8A.5 como transición válida, preservando idempotencia,
  persistencia, entrega y arquitectura común de canales (Fase 8A.6).
- [x] Prohibir libretos conversacionales normales en adaptadores, handlers,
  servicios, tools, graphs y orquestadores, salvo mensajes fijos controlados
  expresamente permitidos (Fase 8A.6).
- [x] Implementar runtime conversacional natural, agnóstico de canal y sin tools
  operativas (Fase 8A.7).
- [x] Implementar tool calling tenant-scoped de servicios, solo lectura (Fase
  8A.8).
- [x] Implementar recolección natural y persistente del contexto inicial de
  reserva (Fase 8A.9).
- [x] Persistir la referencia interna del servicio validado y resolver cambios
  explícitos sin exponer UUID al LLM o al canal (corrección Fase 8A.9).
- [x] Separar propuesta LLM, candidato temporal y selección confirmada por el
  backend, rechazando estados operativos imposibles (corrección Fase 8A.9).
- [x] Preservar selecciones ante consultas informativas y derivar el próximo paso
  conversacional no transaccional (corrección Fase 8A.9).
