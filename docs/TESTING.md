# TESTING.md
# Política de pruebas para TotalChat

## 1. Propósito

Este documento define la política oficial de base de datos para pruebas en TotalChat.

El objetivo es permitir pruebas rápidas y aisladas cuando sea apropiado, sin crear ambigüedad arquitectónica sobre la base de datos soportada por la plataforma.

## 2. Política oficial de base de datos

PostgreSQL es la única base de datos soportada para runtime, integración, staging y producción.

PostgreSQL con pgvector sigue siendo la fuente de verdad de la arquitectura de TotalChat para:

- Datos SaaS compartidos en `public`.
- Datos operativos por schema de tenant.
- Migraciones Alembic.
- Aislamiento multi-tenant por schema PostgreSQL.
- Comportamiento transaccional e integraciones productivas.
- Búsqueda vectorial mediante pgvector.

SQLite no es una base de datos soportada para la arquitectura runtime de TotalChat.

## 3. Uso permitido de SQLite in-memory

SQLite in-memory puede usarse únicamente como test double para pruebas rápidas, aisladas y de bajo alcance, tales como:

- Unit tests que validan lógica de aplicación sin depender de comportamiento específico de PostgreSQL.
- Pruebas simples de API que ejercitan rutas, validaciones, serialización o manejo básico de errores.
- Pruebas que no buscan demostrar migraciones, aislamiento por schema, pgvector, constraints críticos ni semántica transaccional productiva.

Si una prueba usa SQLite in-memory, debe estar intencionalmente acotada como prueba rápida y aislada. Esa prueba no debe presentarse como evidencia de que funciona comportamiento específico de PostgreSQL.

## 4. Cuándo PostgreSQL es obligatorio

Las pruebas deben usar PostgreSQL, no SQLite, cuando validen cualquiera de los siguientes comportamientos:

- Migraciones Alembic o cambios de schema.
- Comportamiento schema-per-tenant.
- Aislamiento de tenants a nivel de base de datos o schema.
- Comportamiento de pgvector.
- Tipos de datos específicos de PostgreSQL.
- Foreign keys, constraints o índices críticos.
- Comportamiento transaccional.
- Concurrencia o locking.
- Comportamiento de integración similar a producción.

En estos casos, SQLite no es un sustituto aceptable porque no reproduce de forma suficiente las garantías, extensiones y semánticas de PostgreSQL que TotalChat requiere.

## 5. Expectativas para revisión de PR

Toda revisión de PR debe verificar que el uso de base de datos respete esta política.

Los revisores deben marcar como desviación de alcance o arquitectura cualquier PR que introduzca SQLite fuera de pruebas, o que use SQLite como alternativa arquitectónica a PostgreSQL.

También deben rechazar pruebas que intenten demostrar comportamiento PostgreSQL-specific usando únicamente SQLite.

## 6. Ejemplos de uso aceptable de SQLite

Ejemplos aceptables:

- Un unit test de un servicio que usa SQLite in-memory para crear datos efímeros y validar una regla de aplicación sin semántica PostgreSQL-specific.
- Una prueba simple de endpoint administrativo que valida status codes, payloads y errores de validación usando una base in-memory aislada.
- Una prueba rápida que no ejecuta migraciones reales ni afirma aislamiento por schema, pgvector, constraints críticos o comportamiento transaccional productivo.

## 7. Ejemplos de uso prohibido de SQLite

SQLite no debe introducirse como:

- Base de datos runtime.
- Base de datos de despliegue.
- Base de datos persistente para la aplicación local.
- Base de datos de tenant.
- Arquitectura alternativa a PostgreSQL.
- Sustituto de pgvector.

También está prohibido usar SQLite como única evidencia para validar:

- Migraciones Alembic.
- Aislamiento schema-per-tenant.
- Aislamiento de tenants a nivel de base de datos o schema.
- Comportamiento pgvector.
- Tipos PostgreSQL-specific.
- Foreign keys, constraints o índices críticos.
- Transacciones, concurrencia o locking.
- Integraciones productivas o production-like.
