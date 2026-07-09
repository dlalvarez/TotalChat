# CONSTITUTION.md  
# Constitución del Proyecto TotalChat

## 1. Propósito

Esta constitución gobierna el desarrollo de TotalChat. Cualquier spec, plan, tarea, pull request o implementación debe respetar estas reglas.

TotalChat será una plataforma conversacional multi-tenant para reservas, iniciando por citas médicas, con backend propio, consola administrativa, PostgreSQL, LangGraph, OpenAI, Telegram, pagos y automatizaciones complementarias.

## 2. Principios no negociables

### 2.1. TotalChat no es solo un bot

TotalChat no debe implementarse como un bot aislado.

Debe ser una plataforma compuesta por:

- Backend de dominio.
- Base de datos.
- Consola administrativa.
- Agente conversacional.
- Canales de mensajería.
- Pagos.
- Automatizaciones complementarias.

El bot es una interfaz conversacional sobre una plataforma de reservas.

### 2.2. PostgreSQL es la fuente de verdad

PostgreSQL será la fuente de verdad para:

- Tenants.
- Organizaciones.
- Sedes.
- Consultorios.
- Profesionales.
- Especialidades.
- Servicios del profesional.
- Tarifas.
- Pacientes.
- Citas.
- Estados de pago.
- Evidencias de pago.
- Revisiones manuales.
- Configuraciones del tenant.
- Conversaciones y mensajes relevantes.
- Documentos semánticos.

Ni el LLM ni n8n son fuente de verdad.

### 2.3. La IA conversa, pero no decide la verdad

La IA puede:

- Entender lenguaje natural.
- Identificar intención.
- Resolver ambigüedades.
- Pedir datos faltantes.
- Presentar servicios.
- Presentar horarios.
- Explicar opciones de pago.
- Guiar la conversación.
- Prevalidar información no crítica, como comprobantes de pago.

La IA no puede inventar ni confirmar:

- Precios.
- Disponibilidad.
- Profesionales.
- Servicios.
- Sedes.
- Consultorios.
- Pagos.
- Citas.
- Links de reunión.
- Reembolsos.
- Estados bancarios.
- Diagnósticos médicos.
- Políticas no configuradas.

Toda acción crítica debe ejecutarse mediante herramientas controladas del backend.

### 2.4. No diagnóstico médico

TotalChat no hará diagnóstico médico.

Puede ayudar administrativamente a reservar citas y orientar dentro de servicios configurados por el tenant, pero no debe afirmar enfermedades, tratamientos, diagnósticos ni decisiones clínicas.

Si el usuario expresa una emergencia, el sistema debe recomendar atención médica inmediata o contacto con servicios de emergencia.

### 2.5. Multi-tenancy desde el inicio

TotalChat debe ser multi-tenant desde el inicio.

Un tenant puede representar:

- Profesional independiente.
- Consultorio privado.
- Médico o especialista particular.
- Clínica.
- Centro médico.
- Organización con varias sedes.
- Organización con varios profesionales.

### 2.6. Schema PostgreSQL por tenant

La arquitectura inicial usará:

- Una aplicación.
- Una base PostgreSQL.
- Schema `public` para control SaaS.
- Un schema PostgreSQL por tenant para datos operativos.

Ejemplo:

```text
public
tenant_dra_ana
tenant_dr_carlos
tenant_clinica_vida
```

El LLM nunca decide qué schema usar. El backend resuelve el tenant y schema antes de ejecutar herramientas.

### 2.7. Consola administrativa obligatoria

La consola administrativa es parte esencial del producto.

Debe permitir que cada tenant gestione:

- Organizaciones.
- Sedes.
- Consultorios.
- Profesionales.
- Especialidades.
- Servicios.
- Tarifas.
- Disponibilidad.
- Citas.
- Pacientes.
- Pagos.
- Links virtuales.
- Políticas.
- Canales.

El bot depende de estos datos para operar.

### 2.8. Deshabilitar antes que eliminar

Para datos maestros y operativos, se debe preferir deshabilitar antes que eliminar.

Aplica a:

- Profesionales.
- Servicios.
- Tarifas.
- Sedes.
- Consultorios.
- Especialidades.
- Pacientes.
- Citas.
- Configuraciones.

### 2.9. La especialidad no define precio

La especialidad clasifica, pero no define precio.

Ejemplos de especialidad:

- Psicología.
- Dermatología.
- Odontología.
- Medicina general.

El precio depende del servicio ofrecido por un profesional y del plan comercial aplicable.

### 2.10. Cada profesional tiene sus propios servicios

Cada profesional define sus propios servicios, duración, modalidad y condiciones.

Dos profesionales de la misma especialidad pueden tener servicios y precios distintos.

### 2.11. Precios por jerarquía comercial flexible

El modelo de precios debe soportar esta jerarquía:

```text
Tipo de pagador
  → Entidad / pagador
    → Plan / producto / convenio
      → Tarifa específica del servicio del profesional
```

Ejemplos:

```text
Particular
  → Particular
    → Tarifa particular

Medicina prepagada
  → Sura
    → Póliza básica
    → Póliza mejorada

Medicina prepagada
  → Colsanitas
    → Plan inicial
    → Plan avanzado

Póliza de salud
  → Aseguradora ABC
    → Plan pequeño
```

El precio final debe configurarse por:

```text
practitioner_service + payer_plan
```

No por tipo general únicamente.

### 2.12. La cita guarda snapshot

Toda cita debe guardar snapshot de:

- Servicio.
- Profesional.
- Duración.
- Modalidad.
- Sede.
- Consultorio.
- Dirección.
- Tipo de pagador.
- Entidad/pagador.
- Plan.
- Precio.
- Moneda.
- Total.

Esto evita que cambios futuros de tarifas modifiquen citas existentes.

### 2.13. Paciente previo no es requisito

El usuario no necesita existir previamente como paciente para reservar.

El bot debe pedir datos mínimos y crear un paciente incompleto si es necesario.

Los datos adicionales se completan antes de la cita, desde la consola administrativa o mediante flujos posteriores.

### 2.14. Datos mínimos configurables

Cada tenant puede configurar qué datos son obligatorios y en qué etapa:

- before_booking
- before_payment
- before_confirmation
- before_appointment
- before_invoice
- at_reception

Por defecto, la reserva debe requerir la mínima información viable.

### 2.15. Citas presenciales y virtuales

TotalChat debe soportar:

- Presencial.
- Virtual.
- Ambas.

El MVP debe permitir links virtuales manuales. La generación automática con Teams, Google Meet, Zoom u otros proveedores será futura.

### 2.16. OpenAI inicial, arquitectura desacoplada

OpenAI será el proveedor LLM inicial.

Debe existir una abstracción `LLMProvider`.

Ollama o modelos locales podrán ser evaluados en laboratorio o fases futuras, pero no son dependencia crítica del MVP.

### 2.17. pgvector desde el inicio

TotalChat usará pgvector desde el inicio para búsqueda semántica sobre:

- Servicios.
- Especialidades.
- Preguntas frecuentes.
- Políticas.
- Instrucciones de pago.
- Instrucciones de llegada.
- Instrucciones de citas virtuales.

pgvector no determina disponibilidad, precio ni pago.

### 2.18. Redis recomendado desde el MVP

Redis podrá usarse para:

- Estado temporal de conversación.
- Holds temporales de slots.
- Locks para evitar doble reserva.
- Rate limiting.
- Cache ligera.
- Futuras colas.

Redis no es fuente de verdad.

### 2.19. Telegram primero

El primer canal será Telegram directo.

WhatsApp se implementará después.

### 2.20. Pagos simulados primero, Wompi después

El MVP usará pagos simulados y flujos manuales.

Wompi se implementará después en sandbox.

### 2.21. Transferencias con revisión humana

Para transferencias:

- El sistema espera evidencia de pago por un tiempo configurable.
- Si no se envía evidencia, la reserva expira y el horario se libera.
- Si se envía evidencia, la reserva queda protegida y pasa a revisión manual.
- La falta de revisión administrativa no debe liberar la reserva salvo configuración explícita.
- Revisión vencida genera alertas y escalamiento.

La IA puede prevalidar comprobantes, pero no confirmar pagos.

### 2.22. Pasarela confirmada puede confirmar automáticamente

Pagos por Wompi u otra pasarela pueden confirmar automáticamente cuando haya webhook/evento confiable validado.

### 2.23. Pago en sitio configurable

Cada tenant define si acepta pago en sitio.

Algunos profesionales pueden requerir pago previo para evitar no-show.

### 2.24. Recordatorios y confirmación de asistencia

TotalChat debe soportar recordatorios por el mismo canal del usuario.

Si el usuario confirma asistencia, la cita se mantiene.

Si responde que no asistirá, se debe pedir una segunda confirmación, advirtiendo:

- El cupo será liberado.
- Una nueva cita dependerá de disponibilidad.
- Si ya pagó, el reembolso se hará según política configurable.

La cancelación por falta de respuesta es configurable, no obligatoria.

### 2.25. n8n complementario

n8n puede enviar recordatorios, alertas, encuestas y notificaciones.

n8n no debe contener la lógica principal de reservas, pagos, disponibilidad, estado de citas o multi-tenancy.

### 2.26. Reglas de no desviación

1. No convertir TotalChat en historia clínica.
2. No implementar diagnóstico médico.
3. No construir carrito/POS en el MVP.
4. No implementar restaurantes antes del MVP médico.
5. No implementar hoteles antes de analizar brechas.
6. No usar n8n como core.
7. No permitir que la IA invente datos críticos.
8. No permitir que la IA elija tenant/schema.
9. No usar tenant_id como único aislamiento principal.
10. No asumir precio único por especialidad.
11. No asumir precio único por servicio del profesional.
12. No limitar precios a solo particular/prepagada/póliza.
13. No confirmar transferencias automáticamente por imagen.
14. No liberar reserva por revisión administrativa vencida salvo configuración explícita.
15. No cancelar por respuesta negativa sin segunda confirmación.
16. No cancelar por falta de respuesta salvo política explícita.
17. No implementar salas automáticas antes de links manuales.
18. No implementar Wompi antes de pagos simulados.
19. No implementar WhatsApp antes de Telegram.
20. No guardar secretos en el repositorio.
21. No eliminar físicamente datos maestros por defecto.
22. No acoplar el código directamente a OpenAI.
23. No usar Redis como fuente de verdad.
24. No usar pgvector para datos transaccionales críticos.
25. No crear un conector rígido exclusivo a Docplanner como parte del core.
26. No hacer que Docplanner sea requisito para operar TotalChat.
27. No mezclar agenda externa y reuniones virtuales en una sola abstracción rígida.
28. No confirmar citas locales para tenants con agenda externa autoritativa sin validación/reserva externa.
29. No reducir el modelo de precios jerárquico de TotalChat para ajustarlo a las limitaciones de Docplanner, Google Calendar o Microsoft.
30. No delegar pagos, revisión manual de transferencias o políticas comerciales a proveedores de calendario.

### 2.27. Integraciones externas de agenda y calendario

TotalChat debe tener motor interno de agenda y reservas, pero la arquitectura debe permitir configurar proveedores externos de agenda/calendario por tenant, organización o profesional.

Docplanner, Google Calendar, Microsoft Calendar y otros sistemas deben implementarse como adaptadores mediante una capa genérica de proveedores, no como dependencias del core.

Reglas:

- TotalChat puede operar con agenda interna sin depender de terceros.
- Un tenant puede configurar una agenda externa como autoridad de disponibilidad.
- Para tenants con agenda externa como autoridad, TotalChat no debe confirmar localmente una cita sin validar, crear o bloquear primero la reserva en el proveedor externo.
- La integración externa no reemplaza pagos, precios, revisión manual, recordatorios, confirmación de asistencia, conversación, consola administrativa ni multi-tenancy.
- Docplanner debe ser una implementación de `SchedulingProvider`, no el diseño completo.
- Google Calendar y Microsoft Calendar deben ser adaptadores equivalentes en la misma capa.

### 2.28. Separación entre agenda y reunión virtual

TotalChat debe separar proveedor de agenda de proveedor de reunión virtual.

- `SchedulingProvider` maneja disponibilidad, reservas, cancelaciones, reprogramaciones y bloqueos.
- `MeetingProvider` maneja links de reunión virtual.

Ejemplos:

- Docplanner puede ser `SchedulingProvider`.
- Google Calendar puede ser `SchedulingProvider`.
- Microsoft Calendar puede ser `SchedulingProvider`.
- Google Meet puede ser `MeetingProvider`.
- Microsoft Teams puede ser `MeetingProvider`.
- Link manual será `ManualMeetingProvider` en MVP.


### 2.29. Estados críticos gobernados por máquinas de estado

Los estados de citas, pagos, evidencias, revisiones, confirmación de asistencia, reembolsos, citas virtuales e integraciones externas no deben modificarse libremente desde controladores o handlers.

Toda transición crítica debe pasar por servicios de dominio y respetar `docs/STATE_MACHINES.md`.

Reglas:

- No cambiar estados críticos con updates directos sin validar transición.
- No confirmar citas saltándose reglas de pago y agenda.
- No marcar pagos como aprobados sin revisión o confirmación válida.
- No cancelar por respuesta negativa sin segunda confirmación.
- No liberar slots protegidos por evidencia enviada salvo configuración explícita.

### 2.30. TotalChat como plataforma paraguas y MediChat como primer vertical

TotalChat debe entenderse como plataforma paraguas y familia de soluciones, no como el nombre exclusivo del producto médico.

Nombres oficiales:

```text
TotalChat  = plataforma paraguas
MediChat   = médicos y profesionales de salud
RestoChat  = restaurantes y bares
HotelChat  = hoteles
StayChat   = Airbnb y otros alojamientos
StoreChat  = tiendas y comercio minorista
```

El primer vertical implementado será MediChat.

Reglas:

- TotalChat Core no debe contener reglas médicas.
- MediChat debe contener el dominio médico.
- RestoChat, HotelChat, StayChat y StoreChat quedan como verticales futuros.
- Nuevos verticales deben implementarse dentro de `solutions/`.
- Funcionalidad común solo debe promoverse a `packages/` si es realmente reusable.

### 2.31. Política de repositorio monorepo modular

TotalChat iniciará como monorepo modular.

Estructura conceptual:

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

Reglas:

- `packages/` contiene capacidades compartidas.
- `solutions/medichat/` contiene dominio médico.
- El core no importa soluciones.
- Las soluciones pueden importar packages.
- Las soluciones no deben importarse entre sí.
- Codex no debe mezclar lógica médica en core.
- Separación futura en repos independientes solo debe hacerse cuando el core y los verticales estén maduros.

### 2.32. Campañas, comunicados y mensajería masiva

TotalChat debe soportar campañas, comunicados y mensajería masiva como capacidad transversal de plataforma, reutilizable por todos los verticales.

Esta capacidad debe permitir:

- crear campañas desde consola admin;
- enviar mensajes inmediatos;
- programar mensajes;
- segmentar audiencias;
- respetar preferencias de contacto;
- respetar consentimiento;
- registrar auditoría;
- registrar entregas individuales;
- medir resultados básicos;
- usar canales configurados como Telegram o WhatsApp futuro.

Reglas:

- Campañas y comunicados no deben ser exclusivos de MediChat.
- Marketing no debe enviarse a contactos sin consentimiento.
- n8n puede ejecutar o complementar, pero no debe ser fuente de verdad.
- El admin debe confirmar explícitamente antes de enviar una campaña.
- Se deben respetar políticas del canal.
