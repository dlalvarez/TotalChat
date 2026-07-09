# ADMIN_CONSOLE.md  
# Consola Administrativa de TotalChat

## 1. Propósito

La consola administrativa es necesaria para que los tenants autogestionen su operación.

El bot no puede funcionar correctamente sin datos maestros.

## 2. Stack recomendado

- React.
- TypeScript.
- Vite.
- Tailwind CSS.
- shadcn/ui.
- TanStack Query.
- React Hook Form.
- Zod.

## 3. Principios de UX/UI para la Consola Administrativa

La consola administrativa de TotalChat/MediChat no debe ser una interfaz meramente técnica ni una simple exposición de endpoints del backend. Debe ser una herramienta profesional, agradable, clara y fácil de usar para usuarios administrativos reales de consultorios, profesionales de salud, clínicas y organizaciones.

La consola debe ocultar la complejidad técnica del backend y presentar una experiencia operativa comprensible. Los identificadores internos como UUIDs pueden existir en la base de datos y en la API, pero no deben ser la forma normal en que el usuario interactúa con el sistema.

### Reglas obligatorias

1. La interfaz debe tener una estética profesional, moderna, limpia y sobria.
2. Los colores deben transmitir confianza, seriedad y claridad operativa.
3. La navegación debe ser clara, accesible y consistente.
4. Los menús deben organizarse según la operación real del usuario, no según la estructura técnica interna.
5. Los formularios no deben exigir que el usuario digite UUIDs para relacionar entidades.
6. Toda relación entre tablas debe resolverse mediante controles amigables como select, dropdown, searchable select, autocomplete o selector asistido.
7. Las listas deben mostrar nombres legibles, estados claros y acciones visibles.
8. Los formularios deben tener labels claros, validación amigable, mensajes de error comprensibles y valores por defecto razonables.
9. La consola debe usar componentes reutilizables para mantener consistencia visual y funcional.
10. La experiencia debe priorizar facilidad de uso, reducción de errores y operación diaria fluida.

### Ejemplos

Cuando un formulario necesite seleccionar una organización, sede, consultorio, profesional, especialidad, servicio, pagador, plan o cita, la interfaz debe mostrar nombres legibles y opciones buscables.

No se debe pedir al usuario algo como:

```text
organization_id = a975b09e-9e45-4ab2-afa4-e81e1e3c6178
```

La interfaz debe mostrar algo como:

```text
Organización: Clínica Vida
```

y resolver internamente el UUID correspondiente.

### Criterio rector

La consola administrativa debe sentirse como un producto SaaS profesional, no como una herramienta técnica interna. El usuario debe poder administrar su operación sin conocer detalles internos de base de datos, UUIDs, rutas API o nombres de tablas.

## 3. Autenticación

Recomendación:

- Email/password.
- JWT access token.
- Refresh token.
- Password hash con Argon2 o bcrypt.
- Roles por tenant.

Roles:

```text
owner
admin
staff
readonly
```

## 4. Módulos

### 4.1. Login y tenant selector

Debe permitir iniciar sesión y seleccionar tenant si el usuario pertenece a varios.

### 4.2. Dashboard

Debe mostrar:

- Citas del día.
- Próximas citas.
- Citas pendientes de pago.
- Citas pendientes de revisión manual.
- Citas virtuales sin link.
- Citas sin confirmación de asistencia.
- Alertas de revisión vencida.
- Alertas de link pendiente.
- Servicios activos.
- Profesionales activos.

### 4.3. Organizaciones

CRUD lógico:

- Crear.
- Consultar.
- Editar.
- Deshabilitar.

### 4.4. Sedes

Debe permitir configurar sedes físicas o virtuales.

Campos:

- Nombre.
- Dirección.
- Ciudad.
- Referencia.
- Instrucciones.

### 4.5. Consultorios

Debe permitir crear consultorios asociados a sedes.

### 4.6. Profesionales

Debe permitir:

- Crear profesional.
- Editar profesional.
- Asociar organización.
- Asociar especialidad.
- Deshabilitar.

### 4.7. Especialidades

Debe permitir crear y administrar especialidades.

### 4.8. Servicios del profesional

Debe permitir:

- Crear servicio por profesional.
- Definir duración.
- Definir descripción.
- Definir si requiere pago.
- Definir modalidad.
- Asociar sede/consultorio.
- Deshabilitar servicio.

### 4.9. Precios y planes

Debe permitir:

- Crear tipos de pagador.
- Crear pagadores.
- Crear planes.
- Asignar precios por servicio del profesional y plan.
- Definir vigencia.
- Deshabilitar tarifas.

Debe soportar jerarquía:

```text
payer_type → payer → payer_plan → price
```

### 4.10. Disponibilidad

Debe permitir:

- Crear reglas semanales.
- Definir profesional.
- Definir servicio o todos.
- Definir sede/consultorio.
- Definir modalidad.
- Definir buffers.
- Crear excepciones.

### 4.11. Citas

Debe permitir:

- Ver citas.
- Crear cita manual.
- Cancelar.
- Reprogramar.
- Ver estado.
- Ver pago.
- Ver confirmación de asistencia.

### 4.12. Pacientes

Debe permitir:

- Ver pacientes.
- Crear/editar.
- Completar datos pendientes.
- Asociar planes/coberturas.
- Ver citas administrativas.
- Deshabilitar.

### 4.13. Pagos

Debe permitir:

- Ver pagos.
- Ver comprobantes.
- Ver prevalidación IA.
- Aprobar.
- Rechazar.
- Solicitar nueva evidencia.
- Marcar revisión bancaria.
- Ver revisión vencida.

### 4.14. Citas virtuales

Debe permitir:

- Ver citas virtuales.
- Ver citas sin link.
- Agregar link manual.
- Editar link.
- Marcar link enviado.
- Reenviar link.

### 4.15. Recordatorios

Debe permitir:

- Configurar recordatorios.
- Configurar confirmación de asistencia.
- Ver no confirmados.
- Ver respuestas negativas pendientes de segunda confirmación.

### 4.16. Configuración del bot

Debe permitir:

- Mensajes base.
- Políticas de pago.
- Políticas de cancelación.
- Instrucciones de llegada.
- Instrucciones de citas virtuales.
- Handoff humano.
- Canal Telegram.
- Futuro WhatsApp.

## Módulo Campañas y comunicados

La consola administrativa debe incluir un módulo transversal:

```text
Campañas y comunicados
```

Pantallas mínimas:

```text
Listado de campañas
Crear campaña
Editar borrador
Seleccionar audiencia
Previsualizar audiencia
Previsualizar mensaje
Enviar ahora
Programar envío
Cancelar programada
Detalle de campaña
Entregas
Métricas
```

Campos:

```text
nombre
descripción
tipo de campaña
tipo de mensaje
solución/vertical
audiencia
filtros
canal
mensaje
modo de envío
fecha programada
timezone
```

Antes de enviar, debe mostrarse una confirmación con:

```text
destinatarios estimados
destinatarios elegibles
bloqueados por consentimiento
bloqueados por política de canal
bloqueados por falta de contacto
mensaje final
usuario responsable
```
