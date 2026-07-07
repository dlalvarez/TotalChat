# Spec 014 — Microsoft Calendar and Teams Adapter

## Objetivo

Implementar Microsoft 365 / Outlook Calendar como proveedor de agenda y Microsoft Teams como proveedor de reuniones virtuales.

## Requisitos funcionales

1. Configurar Microsoft Graph por tenant/profesional.
2. Mapear profesional a calendario Microsoft.
3. Consultar disponibilidad/eventos ocupados.
4. Crear evento Outlook.
5. Cancelar evento.
6. Reprogramar evento.
7. Crear reunión Teams cuando aplique.
8. Guardar external_event_id y meeting_url.
9. Sincronizar cambios básicos.

## Reglas

- Calendar provider y meeting provider son capas separadas.
- Teams no debe confundirse con agenda completa.
- Si Microsoft Calendar es autoridad, TotalChat no confirma sin crear/bloquear evento.
