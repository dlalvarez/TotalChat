# SOLUTION_ARCHITECTURE.md
# Arquitectura multi-solución de TotalChat

## 1. Propósito

Este documento define cómo TotalChat debe soportar múltiples soluciones verticales sin mezclar dominios.

## 2. Modelo conceptual

```text
TotalChat Platform
        │
        ├── TotalChat Core
        │
        ├── MediChat
        ├── RestoChat
        ├── HotelChat
        ├── StayChat
        └── StoreChat
```

## 3. Capas

### 3.1. Platform Layer

Responsable de SaaS y operación común.

Incluye:

- tenants;
- users;
- roles;
- subscriptions;
- auth;
- tenant_solutions;
- billing futuro;
- audit global;
- configuration.

### 3.2. Core Capability Layer

Responsable de capacidades reutilizables.

Incluye:

- conversations;
- AI providers;
- channel providers;
- payment providers;
- scheduling providers;
- meeting providers;
- notifications;
- events;
- audit primitives.

### 3.3. Solution Layer

Responsable de dominio específico.

Incluye:

- MediChat domain.
- RestoChat domain.
- HotelChat domain.
- StayChat domain.
- StoreChat domain.

### 3.4. Application Layer

Responsable de exponer interfaces ejecutables.

Incluye:

- API.
- Admin web.
- Worker.
- Webhooks.
- Future public booking UI.

## 4. Soluciones en public schema

Agregar entidad conceptual:

```text
solutions
├── id
├── code
├── name
├── description
├── status
├── created_at
├── updated_at
```

Códigos:

```text
medichat
restochat
hotelchat
staychat
storechat
```

Entidad:

```text
tenant_solutions
├── id
├── tenant_id
├── solution_id
├── status
├── settings
├── created_at
├── updated_at
```

Esto permite que un tenant tenga una o varias soluciones.

Ejemplo simple:

```text
Tenant Consultorio Ana → MediChat
```

Ejemplo futuro:

```text
Tenant Club Campestre
├── RestoChat
├── HotelChat
└── EventChat futuro
```

Aunque solo MediChat se implemente inicialmente, el modelo debe reconocer que TotalChat es multi-solución.

## 5. Tenant y solución

Un tenant puede tener:

```text
one_solution
multiple_solutions_future
```

Para MVP:

```text
tenant_solutions = medichat
```

## 6. Configuración por solución

Cada solución puede tener settings propios.

Ejemplo MediChat:

```json
{
  "allow_manual_transfer": true,
  "require_payment_before_confirmation": true,
  "default_schedule_authority": "internal"
}
```

Ejemplo RestoChat futuro:

```json
{
  "default_party_size": 2,
  "table_hold_minutes": 15,
  "allow_waitlist": true
}
```

Ejemplo HotelChat futuro:

```json
{
  "check_in_time": "15:00",
  "check_out_time": "11:00",
  "allow_partial_payment": true
}
```

## 7. Admin web multi-solución

La consola admin debe tener:

- shell común;
- navegación común;
- módulos por solución activa;
- permisos por tenant;
- permisos por solución futura.

Ejemplo:

```text
Admin Shell
├── Dashboard platform
├── Settings
├── Users
├── MediChat module
├── RestoChat module futuro
├── HotelChat module futuro
├── StayChat module futuro
└── StoreChat module futuro
```

## 8. Agente conversacional multi-solución

El agente debe resolver:

1. Tenant.
2. Solución activa.
3. Canal.
4. Estado conversacional.
5. Dominio de herramientas.

Ejemplo MediChat:

```text
tenant = consultorio_ana
solution = medichat
agent = MediChatBookingAgent
tools = medichat tools
```

Ejemplo futuro RestoChat:

```text
tenant = restaurante_xyz
solution = restochat
agent = RestoChatReservationAgent
tools = restochat tools
```

## 9. Tools por solución

Herramientas comunes:

```text
send_message
get_tenant_settings
handoff_to_human
create_payment_attempt
submit_payment_evidence
```

Herramientas MediChat:

```text
search_health_services
get_medichat_available_slots
create_medichat_booking
confirm_medichat_booking
cancel_medichat_booking
```

Herramientas RestoChat futuras:

```text
get_available_tables
create_table_reservation
join_waitlist
```

No mezclar tools de verticales.

## 10. Eventos por solución

Eventos comunes:

```text
payment.created
payment.paid
notification.sent
conversation.started
```

Eventos MediChat:

```text
medichat.booking.created
medichat.booking.confirmed
medichat.appointment.reminder_due
```

Eventos RestoChat futuros:

```text
restochat.reservation.created
restochat.reservation.confirmed
```

## 11. Migraciones por solución

Cada solución debe tener migraciones propias.

Ejemplo:

```text
solutions/medichat/migrations/
solutions/restochat/migrations/
```

Las migraciones de tenant deben aplicar:

1. Migraciones core tenant.
2. Migraciones de soluciones activas.

Para MVP:

```text
core tenant migrations
+
medichat migrations
```

## 12. Regla de promoción a core

Una funcionalidad solo debe promoverse a `packages/` si cumple al menos una condición:

1. Es técnica y no depende de dominio vertical.
2. Será usada por más de un vertical.
3. Es una interfaz común necesaria para providers.
4. Es infraestructura transversal.

Ejemplo que sí puede ir a core:

```text
PaymentProvider
```

Ejemplo que no debe ir a core:

```text
payer_plan de medicina prepagada
```

Aunque “pagador” pueda parecer genérico, la jerarquía EPS/póliza/prepagada pertenece inicialmente a MediChat. Solo se generalizará si otro vertical requiere una estructura equivalente.

## 13. Reglas para nombres de carpetas

Usar minúsculas sin guiones para verticales:

```text
medichat
restochat
hotelchat
staychat
storechat
```

Usar snake_case para módulos Python.

Usar kebab-case para carpetas de specs:

```text
003-medichat-booking-domain
```

## 14. Reglas para documentación

Cada solución debe tener:

```text
solutions/<solution>/README.md
solutions/<solution>/docs/CONCEPTS.md
solutions/<solution>/docs/ROADMAP.md
solutions/<solution>/specs/
```

En etapa inicial se puede mantener documentación central, pero se debe marcar qué secciones son platform y cuáles son MediChat.

## 15. Aplicación al estado actual

La documentación existente de citas médicas debe reinterpretarse así:

```text
TotalChat Platform = base común
MediChat = dominio médico ya especificado
```

Por tanto:

- pacientes = MediChat;
- profesionales de salud = MediChat;
- especialidades = MediChat;
- pólizas/EPS/prepagada = MediChat;
- Docplanner = adaptador relevante inicialmente para MediChat;
- pagos, canales, agenda provider y reuniones = capacidades de plataforma/core.

## 16. Campañas por solución

El módulo de campañas es transversal, pero cada vertical puede aportar resolvers de audiencia.

Ejemplo MediChat:

```text
MediChatAudienceResolver
```

Ejemplo futuro RestoChat:

```text
RestoChatAudienceResolver
```

Regla:

```text
packages/campaigns contiene la lógica común.
solutions/<vertical>/campaigns contiene la lógica específica de audiencia.
```
