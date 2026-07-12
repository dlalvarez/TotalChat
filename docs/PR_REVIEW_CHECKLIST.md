# PR_REVIEW_CHECKLIST.md
# Checklist de revisión de Pull Requests para TotalChat

## 1. Propósito

Este checklist debe usarse para revisar cada PR generado por Codex o por cualquier desarrollador.

El objetivo es mantener SDD estricto y evitar desviaciones.

## 2. Checklist general

Antes de aprobar un PR, verificar:

```text
[ ] El PR implementa una spec identificada.
[ ] El PR no implementa funcionalidades fuera de la spec activa.
[ ] El PR respeta docs/CONSTITUTION.md.
[ ] El PR actualiza documentación si introduce decisión nueva.
[ ] El PR tiene pruebas relevantes.
[ ] El PR no rompe pruebas existentes.
[ ] El PR no contiene secretos.
[ ] El PR no contiene datos reales de pacientes.
[ ] El PR no introduce dependencias innecesarias.
[ ] El PR tiene migraciones si modifica base de datos.
[ ] El PR tiene manejo de errores.
[ ] El PR tiene logging razonable sin datos sensibles.
```

## 3. Multi-tenancy

```text
[ ] No usa tenant_id como único aislamiento principal.
[ ] Usa schema por tenant.
[ ] No expone schema_name al frontend ni al LLM.
[ ] Resuelve tenant antes de acceder a datos operativos.
[ ] Verifica permisos del usuario sobre el tenant.
[ ] Incluye tests de aislamiento si toca multi-tenancy.
```

## 4. Dominio de citas

```text
[ ] No confirma citas sin validar disponibilidad.
[ ] Guarda snapshot de servicio, profesional, precio, plan y moneda.
[ ] No asume que el paciente debe existir previamente.
[ ] Permite paciente mínimo/incompleto.
[ ] No ignora modalidad presencial/virtual.
[ ] No salta BookingService para cambiar estados directamente.
[ ] Respeta STATE_MACHINES.md.
```

## 5. Precios

```text
[ ] No coloca precio único rígido en practitioner_services.
[ ] Usa jerarquía payer_type → payer → payer_plan.
[ ] El precio se asocia a practitioner_service + payer_plan.
[ ] Particular se modela como plan.
[ ] No inventa precio si no existe tarifa.
[ ] Guarda snapshot de payer_type, payer, payer_plan y price.
```

## 6. Pagos

```text
[ ] No confirma transferencias automáticamente por evidencia.
[ ] La IA solo prevalida comprobantes.
[ ] La aprobación manual queda registrada por administrador; `confirmed_against_bank` solo bloquea si una spec futura de endurecimiento lo exige.
[ ] Si no hay evidencia en plazo, libera slot según política.
[ ] Si hay evidencia, protege slot.
[ ] Review overdue no libera slot por defecto.
[ ] Registra auditoría de revisión.
```

## 6.1. Pagos manuales/simulados

```text
[ ] No implementa Wompi antes de la fase de pasarela aprobada.
[ ] No permite que IA apruebe pagos.
[ ] Evidencia recibida protege el slot.
[ ] Review overdue no libera slot por defecto.
[ ] Cambios de pago preservan el historial de auditoría.
[ ] Cambios de estado de cita pasan por servicios de dominio.
```

## 7. Recordatorios

```text
[ ] Recordatorio usa canal configurado.
[ ] Respuesta negativa no cancela inmediatamente.
[ ] Pide segunda confirmación.
[ ] Mensaje advierte liberación de cupo y reembolso.
[ ] No respuesta no cancela salvo política explícita.
```

## 8. IA

```text
[ ] No llama OpenAI directamente fuera de LLMProvider.
[ ] No permite que IA elija tenant/schema.
[ ] No permite que IA confirme pagos.
[ ] No permite que IA invente disponibilidad.
[ ] No permite que IA invente precios.
[ ] Tools del agente ejecutan servicios de dominio.
[ ] Se registran tool calls relevantes.
```

## 9. SchedulingProvider / MeetingProvider

```text
[ ] BookingService usa SchedulingProvider o queda preparado para hacerlo.
[ ] No acopla agenda a Docplanner.
[ ] No acopla agenda exclusivamente a implementación interna si la spec requiere abstracción.
[ ] No mezcla MeetingProvider con SchedulingProvider.
[ ] MVP usa InternalSchedulingProvider y ManualMeetingProvider.
[ ] Agenda externa futura no reemplaza pagos/precios/conversación.
```

## 10. Seguridad

```text
[ ] No hay secretos en código.
[ ] No hay tokens en logs.
[ ] Webhooks validan secreto/token.
[ ] Passwords se guardan con hash.
[ ] Endpoints admin requieren auth.
[ ] Acciones críticas quedan auditadas.
```

## 11. Base de datos

```text
[ ] Migraciones son reversibles o tienen estrategia clara.
[ ] Tablas tienen timestamps.
[ ] Tablas críticas tienen status.
[ ] No hay deletes físicos innecesarios.
[ ] Índices razonables para foreign keys y búsquedas principales.
[ ] pgvector se usa solo donde corresponde.
```

## 12. Frontend admin

```text
[ ] Formularios validan campos.
[ ] No muestra datos de otro tenant.
[ ] Maneja errores de API.
[ ] No expone secretos.
[ ] Usa términos consistentes con docs.
[ ] Los CRUD no piden UUIDs al usuario para relaciones.
[ ] Los campos relacionales usan selectores amigables con nombres legibles.
[ ] Las listas muestran etiquetas humanas antes que identificadores internos.
[ ] Las tablas admin funcionales usan nombres legibles como punto de entrada para editar registros.
[ ] Los módulos admin funcionales que superan la línea base de solo creación soportan editar e inactivar.
[ ] La inactivación es reversible salvo que una spec futura indique explícitamente lo contrario.
[ ] La inactivación no ejecuta deletes físicos salvo autorización explícita de una spec futura.
```

## 13. Resultado de revisión

Clasificación sugerida:

```text
APPROVE
REQUEST_CHANGES
COMMENT_ONLY
BLOCKED_BY_SCOPE_DEVIATION
BLOCKED_BY_SECURITY
BLOCKED_BY_DATA_MODEL
```

Si el PR se desvía de la spec:

```text
REQUEST_CHANGES: El PR implementa alcance no autorizado. Debe limitarse a la spec activa o documentar una propuesta de desviación para aprobación.
```

## 14. Marca, verticales y repositorio

```text
[ ] El PR respeta TotalChat como plataforma paraguas.
[ ] El PR trata MediChat como primer vertical médico.
[ ] El PR no implementa lógica médica dentro de packages/core.
[ ] El PR no mezcla dominios entre verticales.
[ ] El PR usa packages/ para capacidades compartidas.
[ ] El PR usa solutions/medichat para dominio médico.
[ ] El PR no implementa RestoChat, HotelChat, StayChat o StoreChat si la spec activa no lo pide.
[ ] El PR no introduce repositorios separados sin decisión aprobada.
```

## 15. Campañas y comunicados

```text
[ ] El PR trata campañas como capacidad transversal de plataforma.
[ ] El PR no implementa campañas solo dentro de MediChat.
[ ] El PR respeta consentimiento de marketing.
[ ] El PR registra entregas individuales.
[ ] El PR audita creación, programación, envío y cancelación.
[ ] El PR no usa n8n como fuente de verdad.
[ ] El PR valida políticas de canal.
[ ] El PR evita envíos duplicados.
[ ] El PR soporta idempotencia o estrategia equivalente.
[ ] El PR no permite que IA envíe campañas sin revisión humana.
```
## 16. Testing database policy

```text
[ ] SQLite appears only in tests, never runtime/deployment config.
[ ] SQLite in-memory tests are limited to fast isolated unit/API tests.
[ ] PostgreSQL is used for migrations, schema-per-tenant, pgvector and integration behavior.
[ ] The PR does not use SQLite as an architectural alternative to PostgreSQL.
[ ] Tests relying on PostgreSQL-specific behavior are not asserted using SQLite only.
```

## Checklist específico Fase 6B.4

- [ ] Especialidades usa nombre como entrada a edición, sin botón `Editar` ni acción `Eliminar`.
- [ ] Inactivar/reactivar especialidad no elimina relaciones existentes.
- [ ] Profesionales permiten múltiples especialidades con chips y nombres legibles.
- [ ] Especialidades inactivas no se ofrecen para nuevas asignaciones, pero se muestran si ya estaban asignadas.
- [ ] `room_type` usa select con catálogo fijo y el backend rechaza valores fuera de catálogo.
- [ ] No se implementaron servicios, precios, disponibilidad, citas, pacientes, pagos ni catálogo global de especialidades.

## Checklist Fase 6B.5 — Relación organización-profesional

- [ ] `organization_practitioners` existe por tenant con única `organization_id + practitioner_id`.
- [ ] API lista relaciones con nombres legibles y sin `schema_name`.
- [ ] API crea/reactiva sin duplicar y valida padres activos.
- [ ] API permite cambiar solo `role`/`status` y no cambia IDs de la pareja.
- [ ] Consola no muestra UUIDs, no muestra botón `Editar` separado y no ofrece eliminar.
- [ ] Consola solo ofrece organizaciones/profesionales activos para nuevas asociaciones.
- [ ] Relaciones existentes se conservan aunque padres queden inactivos.
- [ ] No se implementa CRUD de Servicios en esta fase.
- [ ] Se ejecuta `python3 scripts/check_sdd_scope.py` y pruebas relevantes.


### Fase 6B.6 — Servicios del profesional

- [ ] CRUD de servicios usa nombres legibles y no muestra UUIDs en UI.
- [ ] Crear/reactivar valida organización activa, profesional activo y `organization_practitioners` activa.
- [ ] Inactivar no borra físicamente ni modifica citas/precios futuros.
- [ ] Duplicados se rechazan por organización + profesional + nombre normalizado.
- [ ] No se implementan tarifas, modalidades ni disponibilidad en Servicios.
- [ ] `python3 scripts/check_sdd_scope.py`, backend y frontend fueron ejecutados o documentan bloqueo.


## Checklist Fase 6B.7 — Pagadores y planes

- [ ] CRUD lógico de tipos de pagador, pagadores y planes implementado.
- [ ] Crear/reactivar pagadores requiere tipo activo.
- [ ] Crear/reactivar planes requiere pagador y tipo activos.
- [ ] Históricos permanecen visibles aunque padres estén inactivos.
- [ ] Consola usa nombres legibles y no muestra UUIDs ni `schema_name`.
- [ ] Serializers cargan relaciones explícitamente para respuestas create/update/disable.
- [ ] No se implementan precios, tarifas, disponibilidad, citas ni pagos.
- [ ] `python3 scripts/check_sdd_scope.py`, backend y frontend fueron ejecutados o documentan bloqueo.

## Fase 6B.8 — Checklist específico de precios

- [ ] La pantalla Precios no es placeholder y no muestra UUIDs ni `schema_name`.
- [ ] El menú muestra Pagadores y planes antes de Precios.
- [ ] La UI usa COP como moneda operativa temporal sin selector editable.
- [ ] No se implementan pagos, citas, disponibilidad, facturación ni multi-moneda.
- [ ] Crear/reactivar valida servicio, plan, pagador y tipo activos.
- [ ] No hay solapamientos entre vigencias activas para el mismo servicio y plan.

## Checklist específico Fase 6B.9

- [ ] Disponibilidad base no crea citas, reservas, holds ni slots físicos.
- [ ] `day_of_week` está documentado como `0 = Monday/Lunes` y `6 = Sunday/Domingo` en el contrato admin.
- [ ] Crear/reactivar valida organización, profesional, relación organización-profesional y servicio opcional activos.
- [ ] Reglas activas solapadas se rechazan para la misma combinación de organización, profesional, servicio opcional, día, horario y vigencia.
- [ ] Reglas generales y específicas por servicio pueden coexistir sin resolver prioridad en esta fase.

### Fase 6B.9.1 — Bloqueos e indisponibilidad

La disponibilidad base define elegibilidad de atención. Los bloqueos/indisponibilidades reducen esa elegibilidad para rangos futuros donde un profesional no puede atender, aunque sus reglas recurrentes indiquen que normalmente podría hacerlo. Las reservas, citas y holds serán los registros que ocupen realmente un horario en fases posteriores; esta fase no calcula slots, no crea citas y no crea reservas.

La consola administra bloqueos con profesional, sede opcional, consultorio opcional, inicio, fin, tipo controlado por backend, motivo opcional y estado activo/inactivo. No hay borrado físico. Los tipos de bloqueo del MVP son controlados para preservar semántica operativa y facilitar reglas futuras; la configuración dinámica por tenant queda como mejora futura.
