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
[ ] La aprobación manual exige confirmed_against_bank cuando aplica.
[ ] Si no hay evidencia en plazo, libera slot según política.
[ ] Si hay evidencia, protege slot.
[ ] Review overdue no libera slot por defecto.
[ ] Registra auditoría de revisión.
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
