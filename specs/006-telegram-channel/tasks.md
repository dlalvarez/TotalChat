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
