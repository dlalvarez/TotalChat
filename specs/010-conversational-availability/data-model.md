# Data Model — 010 Conversational Availability

La fase no agrega tablas ni migraciones. Lee las entidades de disponibilidad de
8A.10 y agrega opcionalmente `last_availability_query` al JSON existente de la
conversación. Este resumen contiene nombre legible del servicio, rango ISO y
modalidad; no contiene slots, UUID, tenant ni `schema_name`.
