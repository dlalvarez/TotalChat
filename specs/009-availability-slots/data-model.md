# Data Model 009 — Availability Slots

La fase no agrega tablas ni migraciones. Consume de solo lectura `practitioner_services`, `availability_rules`, `availability_exceptions` y `bookings` dentro del schema tenant ya resuelto. `availability_rules.weekday` usa `0 = lunes` a `6 = domingo`; sede y consultorio son opcionales. `service_modalities` puede existir como configuración complementaria, pero no es prerrequisito para generar slots en Fase 8A.10.
