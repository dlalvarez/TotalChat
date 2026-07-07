# Spec 003 — Booking Domain Core

## Objetivo

Implementar el dominio base de reservas médicas.

## Alcance

- Organizaciones.
- Sedes.
- Consultorios.
- Profesionales.
- Especialidades.
- Servicios del profesional.
- Modalidades.
- Jerarquía comercial.
- Tarifas.
- Pacientes mínimos.
- Disponibilidad.
- Citas.

## Reglas clave

- Especialidad no define precio.
- Servicio pertenece al profesional.
- Precio depende de servicio + payer_plan.
- Cita guarda snapshot.
- Paciente previo no es requisito.

## Criterios

- Crear servicio del profesional.
- Crear plan comercial.
- Crear precio por servicio/plan.
- Crear paciente mínimo.
- Crear cita con snapshot.
