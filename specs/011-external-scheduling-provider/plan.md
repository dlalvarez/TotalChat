# Plan 011 — External Scheduling Provider Abstraction

## Componentes

- SchedulingProvider interface.
- MeetingProvider interface.
- InternalSchedulingProvider.
- ManualMeetingProvider.
- Provider registry.
- scheduling_provider_configs.
- meeting_provider_configs.
- external_systems.
- external mappings.
- external events.
- external sync runs.
- FakeSchedulingProvider.

## Interfaz sugerida

```python
class SchedulingProvider:
    def get_available_slots(self, request): ...
    def create_booking(self, request): ...
    def cancel_booking(self, request): ...
    def reschedule_booking(self, request): ...
    def get_booking(self, request): ...
    def sync_external_events(self, request): ...

class MeetingProvider:
    def create_meeting(self, request): ...
    def update_meeting(self, request): ...
    def cancel_meeting(self, request): ...
    def get_meeting_link(self, request): ...
```

## Riesgos

- Doble reserva.
- Complejidad excesiva temprana.
- Conflictos entre proveedor interno y externo.
- Mala configuración por tenant.

## Estrategia

Crear contratos y provider interno sin implementar proveedores externos reales todavía.
