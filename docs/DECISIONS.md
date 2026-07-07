# DECISIONS.md  
# Decisiones del Proyecto TotalChat

## Decisiones cerradas

| Área | Decisión |
|---|---|
| Nombre | TotalChat |
| Repositorio | TotalChat |
| Vertical inicial | Citas médicas / servicios de salud |
| Backend | FastAPI |
| Base de datos | PostgreSQL |
| Multi-tenancy | Schema por tenant |
| Vector search | pgvector desde el inicio |
| Cache/locks | Redis recomendado |
| IA | LangGraph + LangChain |
| LLM inicial | OpenAI |
| LLM futuro | Ollama/laboratorio o proveedores alternativos mediante LLMProvider |
| Canal inicial | Telegram directo |
| Canal futuro | WhatsApp |
| Pagos iniciales | Simulados y transferencia manual |
| Pasarela futura | Wompi |
| Admin web | React/Vite recomendado |
| Auth admin | JWT email/password recomendado |
| Infra | Linux + Docker Compose + Nginx + Let's Encrypt |
| n8n | Complementario, no core |

## Decisiones de dominio

1. La especialidad no define precio.
2. Cada profesional define sus servicios.
3. El precio se define por servicio del profesional y plan comercial.
4. La jerarquía comercial es `payer_type → payer → payer_plan`.
5. El paciente puede tener planes/coberturas, pero el servicio debe tener tarifa para ese plan.
6. La cita guarda snapshot de servicio, precio y plan.
7. El paciente no necesita existir previamente para reservar.
8. El bot puede crear paciente mínimo/incompleto.
9. Transferencias requieren revisión manual.
10. Evidencia enviada protege el slot.
11. Revisión vencida alerta, no libera automáticamente.
12. Recordatorio puede pedir confirmación de asistencia.
13. Respuesta negativa requiere segunda confirmación.
14. No respuesta se maneja según política del tenant.

## Decisiones abiertas

1. Dominio/subdominio inicial.
2. Modelo OpenAI específico.
3. Modelo embeddings específico.
4. Duración default de hold de pago.
5. Tiempo default para evidencia.
6. Hora default de revisión manual.
7. Política default no respuesta.
8. Diseño visual exacto.
9. Estrategia de backups.
10. CI/CD final.

## Decisión — Capa genérica de proveedores de agenda y reuniones

TotalChat mantendrá un motor interno de agenda, pero debe soportar proveedores externos de agenda/calendario y reuniones virtuales por tenant.

La integración no se diseñará como un conector rígido a Docplanner. Docplanner será una implementación de una capa genérica `SchedulingProvider`.

También deben poder existir:

- GoogleCalendarSchedulingProvider.
- MicrosoftCalendarSchedulingProvider.
- OtherSchedulingProvider.

Para reuniones virtuales se usará una capa separada:

- ManualMeetingProvider.
- GoogleMeetProvider.
- MicrosoftTeamsMeetingProvider.
- ZoomMeetingProvider futuro.

Rationale:

- Muchos médicos ya usan Docplanner/Doctoralia como agenda.
- Otros usan Google Calendar o Microsoft 365.
- Ignorar esas agendas puede generar doble reserva.
- Acoplar TotalChat a Docplanner reduciría el alcance del producto.
- TotalChat debe conservar conversación, pagos, precios jerárquicos, revisión manual, recordatorios y consola administrativa.

Decisión:

- Implementar InternalSchedulingProvider como default.
- Implementar ManualMeetingProvider como MVP.
- Diseñar contratos para proveedores externos desde temprano.
- Implementar Docplanner, Google Calendar y Microsoft en fases futuras.


## Decisión — Capa de precisión ejecutable para Codex

TotalChat mantendrá una capa de documentación adicional para hacer más segura la implementación con Codex:

- Contratos API.
- Máquinas de estado.
- Reglas de proveedores de agenda y reuniones.
- Fixtures de prueba.
- Checklist de PR.

Rationale:

La documentación rectora define alcance y arquitectura, pero Codex implementa mejor cuando cada fase tiene contratos, transiciones, datos de prueba y criterios de revisión explícitos.

Decisión:

Antes de iniciar implementación funcional, se deben agregar y mantener:

```text
docs/API_CONTRACTS.md
docs/STATE_MACHINES.md
docs/SCHEDULING_PROVIDER_RULES.md
docs/TEST_FIXTURES.md
docs/PR_REVIEW_CHECKLIST.md
```

## Decisión — TotalChat como plataforma y verticales oficiales

TotalChat será la marca paraguas y plataforma técnica.

Verticales oficiales:

```text
MediChat   = médicos y profesionales de salud
RestoChat  = restaurantes y bares
HotelChat  = hoteles
StayChat   = Airbnb y otros alojamientos
StoreChat  = tiendas y comercio minorista
```

El primer vertical implementado será MediChat.

Rationale:

El nombre TotalChat es amplio y sirve mejor como marca/familia de soluciones. Los clientes entenderán mejor soluciones especializadas por vertical.

Decisión:

- Mantener repositorio inicial `TotalChat`.
- Organizar internamente con `apps/`, `packages/` y `solutions/`.
- Implementar primero `solutions/medichat/`.
- Documentar RestoChat, HotelChat, StayChat y StoreChat como verticales futuros.

## Decisión — Monorepo modular preparado para separación futura

TotalChat iniciará en monorepo modular.

Rationale:

- Un solo desarrollador al inicio.
- Core todavía en definición.
- MediChat será el primer vertical.
- Separar repos prematuramente aumentaría complejidad.
- Codex y SDD funcionan mejor inicialmente con contexto unificado.

Decisión:

Usar estructura:

```text
apps/
packages/
solutions/
docs/
specs/
infra/
scripts/
tests/
```

Separar repos en el futuro solo cuando existan clientes, equipos, releases o roadmaps independientes por vertical.

## Decisión — Campañas y comunicados como capacidad transversal

TotalChat incluirá un módulo transversal de campañas, comunicados y mensajería masiva.

Rationale:

Todos los verticales necesitan enviar mensajes masivos o segmentados: avisos operativos, promociones, cambios de horario, cierres temporales, apertura de agenda, recordatorios generales o información relevante.

Decisión:

- El módulo vivirá como capacidad de plataforma/core.
- La primera implementación será utilizada por MediChat.
- Los resolvers de audiencia serán específicos por vertical.
- Los canales serán provistos por `ChannelProvider`.
- Se debe respetar consentimiento.
- Se deben registrar entregas individuales.
- n8n puede complementar, pero TotalChat será fuente de verdad.
