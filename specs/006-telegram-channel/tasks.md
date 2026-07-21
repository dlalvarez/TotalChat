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
- [x] Interpretar intención y datos explícitos mediante el provider LLM configurado (Fase 8A.6).
- [x] Validar servicios mencionados con tools tenant-scoped y persistir progreso conversacional (Fase 8A.6).
- [x] Cubrir saludo, servicio único, estado parcial y ambigüedad sin crear reservas (Fase 8A.6).
- [x] Mantener contratos y orquestador 8A.6 agnósticos al canal con estado allowlisted.
- [x] Preservar Booking Agent 7A.9 como capa operativa posterior, sin invocarlo desde 8A.6.
