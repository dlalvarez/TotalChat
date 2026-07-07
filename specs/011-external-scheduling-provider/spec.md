# Spec 011 — External Scheduling Provider Abstraction

## Objetivo

Permitir que TotalChat use proveedores internos o externos de agenda/calendario por tenant sin acoplar el core a un proveedor específico.

## Problema

Algunos profesionales ya usan agendas externas como Docplanner, Google Calendar o Microsoft 365. Si TotalChat crea reservas sin consultar esas agendas, se pueden generar dobles reservas.

## Solución

Crear abstracciones:

```text
SchedulingProvider
MeetingProvider
```

Implementar inicialmente:

```text
InternalSchedulingProvider
ManualMeetingProvider
FakeSchedulingProvider para pruebas
```

## Requisitos funcionales

1. El tenant puede operar con agenda interna.
2. El tenant puede configurar proveedor externo futuro.
3. BookingService puede consultar disponibilidad mediante provider.
4. BookingService puede crear reserva mediante provider.
5. BookingService puede cancelar/reprogramar mediante provider.
6. El sistema puede guardar mappings externos.
7. El sistema puede registrar eventos externos.
8. El sistema puede registrar sync runs.
9. El sistema separa agenda de reunión virtual.

## Requisitos no funcionales

1. No acoplar core a Docplanner.
2. No permitir que LLM llame APIs externas directamente.
3. Toda integración debe mantener contexto tenant.
4. Deben existir tests con provider fake.
5. El MVP debe seguir funcionando sin proveedores externos.

## Fuera de alcance

- Implementación real Docplanner.
- Implementación real Google Calendar.
- Implementación real Microsoft.
- Sincronización bidireccional completa.
