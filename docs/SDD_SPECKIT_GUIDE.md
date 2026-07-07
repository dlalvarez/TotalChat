# SDD_SPECKIT_GUIDE.md  
# Guía para SDD y Spec Kit en TotalChat

## 1. Enfoque

TotalChat se desarrollará bajo un enfoque SDD.

Flujo:

```text
Spec → Plan → Tasks → Implement
```

La especificación gobierna la implementación.

## 2. Artefactos

Cada feature importante debe tener carpeta en `specs/`.

Estructura:

```text
specs/NNN-feature-name/
├── spec.md
├── plan.md
├── tasks.md
├── data-model.md
├── contracts.md
└── quickstart.md
```

## 3. Specs iniciales

1. 001-project-foundation
2. 002-multitenancy
3. 003-booking-domain
4. 004-admin-console
5. 005-langgraph-agent
6. 006-telegram-channel
7. 007-payments-manual-review
8. 008-reminders-confirmation

## 4. Regla de implementación

Codex no debe implementar código fuera del scope de la spec activa.

Si una tarea requiere desviación, debe documentarse y solicitar aprobación.

## 5. Definition of Ready

Una spec está lista si tiene:

- Objetivo.
- Historias de usuario.
- Requisitos funcionales.
- Requisitos no funcionales.
- Fuera de alcance.
- Criterios de aceptación.
- Riesgos.
- Dependencias.

## 6. Definition of Done

Una implementación está lista si:

- Cumple spec.
- Tiene pruebas.
- No viola constitución.
- No introduce alcance no autorizado.
- Documenta decisiones nuevas.
- Pasa lint/tests.
- Tiene migraciones si aplica.
- Tiene quickstart si aplica.

## 7. Prompt inicial para Spec Kit

```text
Crea la especificación 001 para la fundación de TotalChat.

TotalChat es una plataforma conversacional multi-tenant de reservas, iniciando por citas médicas, con FastAPI, PostgreSQL, schema por tenant, pgvector, Redis, LangGraph, OpenAI, Telegram, consola administrativa, pagos simulados, transferencias con revisión manual, recordatorios y n8n complementario.

La Spec 001 debe limitarse a fundación técnica: estructura repo, FastAPI, frontend base, Docker Compose, PostgreSQL, pgvector, Redis, healthcheck, configuración, logging y documentación base.

No implementar todavía dominio de citas, Telegram, pagos ni agente completo.
```

## 8. Specs adicionales para integraciones externas

Las integraciones externas de agenda y reuniones deben manejarse mediante specs separadas:

```text
011-external-scheduling-provider
012-docplanner-adapter
013-google-calendar-adapter
014-microsoft-calendar-teams-adapter
```

Regla:

- La Spec 011 diseña la abstracción genérica.
- Las Specs 012, 013 y 014 implementan adaptadores concretos.
- Ningún adaptador concreto debe modificar la constitución ni acoplar el core a un proveedor.


## Capa de precisión para Codex

Además de specs, planes y tareas, TotalChat debe mantener documentos ejecutables que reduzcan ambigüedad:

- `docs/API_CONTRACTS.md`
- `docs/STATE_MACHINES.md`
- `docs/SCHEDULING_PROVIDER_RULES.md`
- `docs/TEST_FIXTURES.md`
- `docs/PR_REVIEW_CHECKLIST.md`

Antes de pedir implementación a Codex, la spec activa debe revisar estos documentos y declarar cuáles aplican.

Regla:

```text
Codex no debe inferir libremente contratos, rutas, transiciones de estado ni fixtures cuando estos documentos ya los definen.
```

## Flujo recomendado de implementación por PR

```text
1. Seleccionar spec activa.
2. Confirmar que la spec no viola CONSTITUTION.md.
3. Revisar API_CONTRACTS.md si aplica.
4. Revisar STATE_MACHINES.md si aplica.
5. Revisar SCHEDULING_PROVIDER_RULES.md si toca agenda.
6. Revisar TEST_FIXTURES.md para pruebas.
7. Implementar tareas de tasks.md.
8. Ejecutar pruebas.
9. Revisar PR con PR_REVIEW_CHECKLIST.md.
```
