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

Nota de desarrollo: el servidor Vite debe enlazar por defecto a `127.0.0.1` para flujos con SSH tunneling. Cualquier modo público debe ser explícito y temporal.


## 2.1. Fase 6A — Shell administrativo y base UX/UI

La Fase 6A entrega la base reutilizable de la consola administrativa, no los CRUD completos. Su alcance incluye el shell visual, login placeholder, dashboard MVP, navegación principal, estados de interfaz y patrones de componentes para que las pantallas de Fase 6B–6E puedan construirse de forma consistente.

Principios específicos de esta base:

- La interfaz debe verse como un SaaS profesional para clínicas, consultorios y organizaciones de salud.
- Los módulos de negocio que aún no corresponden a Fase 6A deben quedar como placeholders claros, deshabilitados u omitidos, sin implementar comportamiento funcional prematuro.
- Los componentes reutilizables deben cubrir encabezados de página, tarjetas de sección, tablas, estados vacíos, estados de carga, estados de error, campos de formulario, botones de acción, badges, búsqueda y selectores.
- Los campos relacionales deben preparar selectores por nombre o resumen humano: organización por nombre, profesional por nombre completo, plan por pagador/plan legible y cita por paciente/fecha/servicio.
- Los UUIDs pueden viajar por API y estado interno, pero no deben ser solicitados como entrada normal a usuarios administrativos.
- Las pantallas deben mostrar etiquetas humanas, estados comprensibles y acciones operativas claras.


## 2.3. Fase 6B.2 — Consultorios y Profesionales funcionales

La Fase 6B.2 agrega los módulos funcionales de Consultorios y Profesionales siguiendo los patrones de integración frontend de Organizaciones y Sedes.

- Consultorios consulta y crea registros contra el backend usando una sede seleccionada por nombre legible desde un dropdown poblado con sedes reales.
- Profesionales consulta y crea datos básicos del profesional con campos administrativos legibles.
- La asignación de especialidades, servicios, precios, disponibilidad y citas permanece diferida para fases posteriores.
- Los UUIDs continúan siendo identificadores internos: pueden viajar por API y estado de la aplicación, pero no se solicitan como entrada normal del usuario.


## 2.4. Fase 6B.3 — Edición e inactivación de módulos base

La Fase 6B.3 completa la línea base operativa de los módulos funcionales existentes: Organizaciones, Sedes, Consultorios y Profesionales. Estos módulos ahora deben soportar edición de datos administrativos y acciones de deshabilitar/inactivar cuando el backend lo permite o mediante endpoints estrechos consistentes con el estilo admin existente.

- La edición de organizaciones, sedes, consultorios y profesionales inicia desde el nombre legible de cada registro en la tabla, no desde UUIDs ni botones técnicos separados.
- La eliminación física se evita intencionalmente para proteger auditoría, historial operativo y relaciones futuras.
- La inactivación/deshabilitación es la opción preferida para datos maestros como organizaciones, sedes, consultorios y profesionales.
- La inactivación es reversible desde la tabla mediante la acción Activar para registros inactivos.
- Los UUIDs continúan siendo internos: las relaciones se gestionan con selectores legibles por nombre y las tablas muestran nombres humanos como punto de entrada.
- En Consultorios, el campo “Tipo de consultorio” debe explicar ejemplos como Consulta general, Procedimientos, Terapia, Diagnóstico, Virtual u Otro.
- En Consultorios, el campo “Capacidad” debe aclarar que para un consultorio individual normalmente se usa 1 y que puede quedar vacío cuando no aplica.

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

## 4. Autenticación

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


## 4.0. Provisioning operativo de tenants (Fase 6C.1.1)

Antes de crear el primer usuario owner, el tenant debe existir en `public.tenants` y contar con su schema PostgreSQL por tenant. El procedimiento operativo soportado es exclusivamente CLI backend; no existe endpoint HTTP, self-service signup ni pantalla SaaS de gestión de tenants en esta fase.

El comando idempotente es:

```bash
python3 -m app.tenancy.create_tenant \
  --name "Clínica Demo" \
  --slug clinica-demo
```

Reglas operativas:

- `schema_name` se genera internamente desde el `slug`; el comando no acepta ni muestra `schema_name`.
- Si el tenant no existe, crea `public.tenants`, crea el schema tenant y aplica migraciones base y de dominio booking.
- Si el tenant activo ya existe, no duplica registros ni modifica su `schema_name`; verifica/crea el schema faltante y reaplica migraciones idempotentes.
- Si el tenant existe inactivo, falla con mensaje claro y no lo reactiva automáticamente.
- La salida segura contiene solo `tenant_id`, `slug`, `status` y `actions`.

Ejemplo operativo para `tc-dev-01`:

```bash
cd ~/projects/totalchat/backend
source .venv/bin/activate

POSTGRES_DB="$(grep '^POSTGRES_DB=' ~/docker/totalchat/.env | cut -d= -f2-)"
POSTGRES_USER="$(grep '^POSTGRES_USER=' ~/docker/totalchat/.env | cut -d= -f2-)"
POSTGRES_PASSWORD="$(cat ~/docker/totalchat/secrets/postgres_password.txt)"

export TOTALCHAT_DATABASE_URL="postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@127.0.0.1:5432/${POSTGRES_DB}"

python3 -m app.tenancy.create_tenant \
  --name "Clínica Demo" \
  --slug clinica-demo
```

Salida esperada:

```text
Tenant provisioning completed
tenant_id=<uuid>
slug=clinica-demo
status=active
actions=tenant_created,schema_created,migrations_applied
```

Después del provisioning del tenant, crear el owner con el bootstrap operativo existente:

```bash
export TOTALCHAT_BOOTSTRAP_ADMIN_PASSWORD="cambiar-en-operacion"

python3 -m app.auth.create_admin_user \
  --tenant-slug clinica-demo \
  --email admin@clinica-demo.com \
  --full-name "Admin Clínica Demo" \
  --role owner

unset TOTALCHAT_BOOTSTRAP_ADMIN_PASSWORD
```

## 4.1. Bootstrap operativo del primer usuario owner (Fase 6C.1)

Antes de habilitar login real, TotalChat permite crear de forma controlada el primer usuario administrativo de un tenant mediante un comando backend interno. Este mecanismo prepara `public.users` y `public.user_tenants`; no crea endpoints públicos, no implementa pantalla de login, no emite JWT y no toca schemas tenant.

Roles permitidos:

```text
owner
admin
staff
readonly
```

El rol por defecto del bootstrap es `owner`. El comando acepta tenant por `tenant_slug` o `tenant_id`, valida que exista y esté activo, crea el usuario si no existe, actualiza datos seguros como `full_name`, reactiva usuario/vínculo como comportamiento explícito de bootstrap, y crea o reactiva el vínculo del usuario con el tenant. Nunca acepta ni muestra `schema_name`.

Ejemplo operativo para `tc-dev-01`:

```bash
cd ~/projects/totalchat/backend
source .venv/bin/activate

POSTGRES_DB="$(grep '^POSTGRES_DB=' ~/docker/totalchat/.env | cut -d= -f2-)"
POSTGRES_USER="$(grep '^POSTGRES_USER=' ~/docker/totalchat/.env | cut -d= -f2-)"
POSTGRES_PASSWORD="$(cat ~/docker/totalchat/secrets/postgres_password.txt)"

export TOTALCHAT_DATABASE_URL="postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@127.0.0.1:5432/${POSTGRES_DB}"
export TOTALCHAT_BOOTSTRAP_ADMIN_PASSWORD="cambiar-en-operacion"

python3 -m app.auth.create_admin_user \
  --tenant-slug clinica \
  --email admin@clinica.com \
  --full-name "Admin Clínica" \
  --role owner
```

Si `TOTALCHAT_BOOTSTRAP_ADMIN_PASSWORD` no está definida, el comando solicita la contraseña con prompt seguro y confirmación. La salida operativa muestra email, tenant, rol y acciones realizadas; nunca imprime contraseña, hash ni `schema_name`.

## 5. Módulos

### 5.1. Login y tenant selector

Debe permitir iniciar sesión y seleccionar tenant si el usuario pertenece a varios.

### 5.2. Dashboard

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

### 5.3. Organizaciones

CRUD lógico:

- Crear.
- Consultar.
- Editar.
- Deshabilitar.

### 5.4. Sedes

Debe permitir configurar sedes físicas o virtuales.

Campos:

- Nombre.
- Dirección.
- Ciudad.
- Referencia.
- Instrucciones.

### 5.5. Consultorios

Debe permitir crear consultorios asociados a sedes.

### 5.6. Profesionales

Debe permitir:

- Crear profesional.
- Editar profesional.
- Asociar organización.
- Asociar especialidad.
- Deshabilitar.

### 5.7. Especialidades

Debe permitir crear y administrar especialidades.

### 5.8. Servicios del profesional

Debe permitir:

- Crear servicio por profesional.
- Definir duración.
- Definir descripción.
- Definir si requiere pago.
- Definir modalidad.
- Asociar sede/consultorio.
- Deshabilitar servicio.

### 5.9. Precios y planes

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

### 5.10. Disponibilidad

Debe permitir:

- Crear reglas semanales.
- Definir profesional.
- Definir servicio o todos.
- Definir sede/consultorio.
- Definir modalidad.
- Definir buffers.
- Crear excepciones.

### 5.11. Citas

Debe permitir:

- Ver citas.
- Crear cita manual.
- Cancelar.
- Reprogramar.
- Ver estado.
- Ver pago.
- Ver confirmación de asistencia.

### 5.12. Pacientes

Debe permitir:

- Ver pacientes.
- Crear/editar.
- Completar datos pendientes.
- Asociar planes/coberturas.
- Ver citas administrativas.
- Deshabilitar.

### 5.13. Pagos

Debe permitir:

- Ver pagos.
- Ver comprobantes.
- Ver prevalidación IA.
- Aprobar.
- Rechazar.
- Solicitar nueva evidencia.
- Marcar revisión bancaria.
- Ver revisión vencida.

### 5.14. Citas virtuales

Debe permitir:

- Ver citas virtuales.
- Ver citas sin link.
- Agregar link manual.
- Editar link.
- Marcar link enviado.
- Reenviar link.

### 5.15. Recordatorios

Debe permitir:

- Configurar recordatorios.
- Configurar confirmación de asistencia.
- Ver no confirmados.
- Ver respuestas negativas pendientes de segunda confirmación.

### 5.16. Configuración del bot

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

## 6. Fase 6B.1 — Organizaciones y Sedes funcionales

La Fase 6B.1 convierte Organizaciones y Sedes en los primeros módulos funcionales reales de la consola administrativa. Esta fase mantiene la autenticación como placeholder, pero establece el patrón reutilizable para los siguientes CRUD: cliente API frontend configurable por `VITE_TOTALCHAT_API_BASE_URL`, envío del header `X-TotalChat-Tenant-Id`, manejo amigable de errores, consultas y mutaciones con TanStack Query, y formularios con React Hook Form + Zod.

Organizaciones y Sedes consumen los endpoints backend existentes bajo `/api/admin`. La creación de Sedes usa un selector de Organización con nombres legibles obtenido desde datos reales del backend; el UUID de la organización se conserva únicamente como valor interno enviado a la API.

Los UUIDs de tenant, organización y otras relaciones siguen siendo identificadores internos. No deben solicitarse como entrada normal a usuarios administrativos.

## Fase 6B.4 — Especialidades y tipos de consultorio

La consola administrativa incorpora el módulo funcional **Especialidades** con el mismo patrón aprobado para datos maestros: el nombre legible abre la edición, no existe botón separado `Editar`, no hay eliminación física y la acción del extremo derecho alterna entre `Inactivar` y `Activar` según el estado.

Los profesionales pueden tener cero, una o múltiples especialidades. La asignación se gestiona desde el formulario de profesionales mediante búsqueda por nombre y chips; las especialidades inactivas ya asignadas se muestran con indicación visual, pero no se ofrecen como nuevas opciones.

El campo **Tipo de consultorio** deja de ser texto libre en creación y edición. La interfaz usa el catálogo fijo: `consulta_general` (Consulta general), `procedimientos` (Procedimientos), `terapia` (Terapia), `diagnostico` (Diagnóstico), `virtual` (Virtual) y `otro` (Otro). Los valores históricos desconocidos se preservan al listar; nuevas escrituras deben usar valores del catálogo.

## Fase 6B.5 — Profesionales por organización

La consola administrativa agrega una pantalla `Profesionales por organización` para gestionar la relación organización-profesional antes del CRUD de Servicios.

UX implementada:

- Listado con Organización, Profesional, Rol, Estado y Acciones.
- Asociación mediante selectores por nombre; los UUIDs quedan internos y no se muestran al usuario.
- Solo organizaciones y profesionales activos se ofrecen para nuevas relaciones.
- Rol con catálogo fijo y etiquetas: Principal (`primary`), Miembro (`member`) y Externo (`external`).
- El nombre legible de la pareja abre edición del rol; no hay botón separado `Editar`.
- Acciones reversibles `Activar` / `Inactivar`; no hay eliminación física.
- Las relaciones existentes siguen visibles aunque la organización o el profesional queden inactivos, mostrando esa condición en los nombres/estados legibles.

Servicios del profesional permanecen fuera de alcance hasta Fase 6B.6.


## Fase 6B.6 — Servicios

La página Servicios deja de ser placeholder y permite listar, crear, editar, inactivar y reactivar servicios del profesional. La creación selecciona organización activa por nombre y profesional filtrado por relación activa en Profesionales por organización. La edición muestra organización y profesional como contexto legible y no permite cambiar esa pareja; si hubo error, se inactiva y se crea un nuevo servicio. No se muestran UUIDs al usuario, no hay botón Eliminar y las acciones son Inactivar/Activar.

Si una organización, profesional o relación se inactiva después de crear el servicio, el servicio histórico sigue visible con estados legibles. Esta fase excluye precios, modalidades, disponibilidad, pagos y especialidad por servicio.

## Fase 6B.7 — Pagadores y planes

La consola incorpora la página **Pagadores y planes** para administrar exclusivamente la base comercial `Tipo de pagador → Pagador → Plan`. La pantalla se divide en tres secciones: tipos de pagador, pagadores y planes. Los nombres legibles abren edición, la acción derecha permite `Inactivar` / `Activar`, los selectores muestran nombres y los UUIDs permanecen internos.

Reglas implementadas: los pagadores solo se crean o reactivan bajo tipos activos; los planes solo se crean o reactivan bajo pagadores activos cuyo tipo también esté activo; los históricos permanecen visibles si un padre queda inactivo. Esta fase no configura precios, tarifas, disponibilidad, citas ni pagos.

## Fase 6B.8 — Precios / tarifas

La opción **Precios** de la consola deja de ser placeholder y administra tarifas manuales bajo el modelo **Servicio del profesional + Plan del pagador = Precio**. El menú administrativo ordena primero **Servicios**, luego **Pagadores y planes**, luego **Precios**, y mantiene diferidas **Disponibilidad**, **Citas**, **Pagos** y **Configuración**.

La pantalla permite listar, crear, editar, inactivar y reactivar precios con nombres legibles de organización, profesional, servicio, tipo de pagador, pagador y plan. No expone UUIDs ni `schema_name` al usuario final. En edición quedan bloqueados servicio, plan y moneda; si se eligió mal servicio o plan, se debe inactivar el precio y crear uno nuevo.

### Moneda operativa

TotalChat / MediChat maneja una moneda operativa única por tenant. La multi-moneda dentro de un mismo tenant queda fuera del MVP. Como todavía no existe configuración formal de tenant, en esta fase la consola usa **COP** como default técnico temporal, muestra COP como contexto y envía `currency = "COP"` al crear precios. No hay selector de moneda por tenant, organización ni precio; tampoco tasas de cambio ni conversión.

## 5.9.1. Disponibilidad base — Fase 6B.9

La pantalla **Disponibilidad** permite administrar reglas recurrentes de atención para un profesional dentro de una organización, con servicio opcional o alcance **Todos los servicios**. La edición bloquea organización, profesional y servicio para preservar trazabilidad; si la asociación fue incorrecta, se inactiva la regla y se crea una nueva.

La pantalla no muestra UUIDs, no crea citas, no crea reservas, no crea holds, no genera slots físicos y no implementa calendario visual. La convención visible es `0 = Lunes` y `6 = Domingo`.

### Fase 6B.9.1 — Bloqueos e indisponibilidad

La disponibilidad base define elegibilidad de atención. Los bloqueos/indisponibilidades reducen esa elegibilidad para rangos futuros donde un profesional no puede atender, aunque sus reglas recurrentes indiquen que normalmente podría hacerlo. Las reservas, citas y holds serán los registros que ocupen realmente un horario en fases posteriores; esta fase no calcula slots, no crea citas y no crea reservas.

La consola administra bloqueos con profesional, sede opcional, consultorio opcional, inicio, fin, tipo controlado por backend, motivo opcional y estado activo/inactivo. No hay borrado físico. Los tipos de bloqueo del MVP son controlados para preservar semántica operativa y facilitar reglas futuras; la configuración dinámica por tenant queda como mejora futura.

## Fase 6B.10 — Citas administrativas base con agenda diaria

La consola agrega el módulo **Citas** después de Disponibilidad y antes de Pagos. La pantalla separa filtros, navegación de fecha, formulario guiado, **Agenda diaria** y **Listado** para evitar una pantalla monolítica y dejar preparada una evolución futura hacia calendario visual.

Alcance implementado en esta fase:

- creación administrativa de citas desde selects con nombres legibles;
- consulta por fecha seleccionada en agenda diaria;
- listado administrativo filtrable;
- acciones de estado: cancelar, marcar atendida y marcar no asistió;
- visualización conjunta de citas y bloqueos activos como eventos temporales ordenados por inicio.

La agenda diaria no implementa calendario semanal/mensual, drag and drop, resize, integraciones externas ni motor público avanzado de slots. Es una base preparatoria para una fase futura de calendario visual.

### Operación — migraciones tenant bajo demanda

Cuando una fase agrega o modifica columnas/tablas tenant, las migraciones para tenants existentes deben ejecutarse explícitamente. El backend no altera todos los schemas de tenant de forma silenciosa en cada arranque normal.

Procedimiento esperado en `tc-dev-01`:

```bash
cd ~/projects/totalchat/backend
source .venv/bin/activate

POSTGRES_DB="$(grep '^POSTGRES_DB=' ~/docker/totalchat/.env | cut -d= -f2-)"
POSTGRES_USER="$(grep '^POSTGRES_USER=' ~/docker/totalchat/.env | cut -d= -f2-)"
POSTGRES_PASSWORD="$(cat ~/docker/totalchat/secrets/postgres_password.txt)"

export TOTALCHAT_DATABASE_URL="postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@127.0.0.1:5432/${POSTGRES_DB}"

python3 -m app.tenancy.migrate_existing_tenants
```

El comando es idempotente: valida schemas tenant, asegura `tenant_schema_migrations`, aplica migraciones pendientes como `007_booking_notes` con `ADD COLUMN IF NOT EXISTS`/`ON CONFLICT DO NOTHING`, y muestra por consola qué schemas quedaron actualizados o al día.

### Ajustes UX Fase 6B.10

La agenda diaria de Citas muestra espacios `Disponible` explícitos a partir de disponibilidad base activa del profesional seleccionado y siempre construye la línea temporal desde esos slots base. Las citas `scheduled` y los bloqueos activos se superponen sobre los slots derivados de disponibilidad usando intervalos semiabiertos `[inicio, fin)`: un evento que termina exactamente al inicio de un slot no ocupa ese slot. La agenda filtra las citas por fecha seleccionada y solo trata `scheduled` como ocupación real en esta fase, por lo que citas de otra fecha o estados `tentative`, `cancelled`, `completed` y `no_show` no bloquean slots. Si no hay profesional seleccionado, la pantalla pide seleccionar uno para calcular espacios; si no hay disponibilidad base para el día, muestra un mensaje claro. Las tarjetas se compactan para mostrar hora, badge, paciente/profesional/servicio/sede/consultorio sin UUIDs.

La edición administrativa permite reprogramar citas `scheduled` con fecha, hora y consultorio, y editar notas. Citas `cancelled`, `completed` y `no_show` solo permiten editar notas desde la UI.

## Fase 6B.11 — Pagos administrativos base

La consola agrega la pantalla **Pagos** después de **Citas** para consultar intentos de pago asociados a citas y registrar revisión manual básica. La pantalla permite filtrar por organización, método, estado, rango de fechas y texto de paciente; muestra resumen operativo, listado, detalle, evidencias asociadas y revisiones previas.

Las acciones disponibles son aprobar o rechazar únicamente intentos `transfer` con evidencia recibida; el backend ejecuta la transición mediante `PaymentReviewService`. El rechazo exige motivo. La UI muestra nombres legibles y oculta identificadores técnicos como información principal; no expone `schema_name` ni descarga archivos de evidencia.

### Ajustes UX PR #44 — Pagos

La pantalla Pagos prioriza el resumen operativo antes de filtros para que el administrador vea primero volumen total, pendientes de revisión, aprobados, rechazados y vencidos sin evidencia. El estado `expired` se presenta como vencido por falta de evidencia y no es aprobable directamente. Los intentos `transfer` con `evidence_received` siguen siendo revisables aunque la revisión administrativa se demore.

La consola puede registrar un intento manual tipo `transfer` desde una cita existente usando un selector legible de cita/paciente/profesional/fecha/servicio. Si el administrador registra referencia o notas de evidencia, se reutiliza el endpoint existente de evidencia para dejar el intento en `evidence_received`; la aprobación/rechazo posterior continúa pasando por `PaymentReviewService`.

## Fase 6B.12 — Pacientes administrativos base

La consola incluye una pantalla administrativa de Pacientes ubicada antes de Citas en la navegación operativa. Permite listar, crear, consultar, editar, inactivar y reactivar pacientes del tenant actual.

Alcance explícito de esta fase:

- Datos administrativos básicos: nombre completo, tipo/número de documento, teléfono, email y estado de perfil.
- `document_type` usa catálogo controlado Colombia/MVP con valores `RC`, `TI`, `CC`, `PAS`, `CE`, `RE`, `PPT`, `SC`, `DNI`, `NIT`, `OTHER`; `OTHER` es escape operativo controlado, sin campo adicional de texto libre.
- Creación desde consola con `created_from_channel = admin` y `profile_status = minimal`.
- Inactivación lógica mediante `profile_status = inactive`; no existe borrado físico.
- Reactivación mediante actualización de `profile_status` a un estado permitido no inactivo, usando `minimal` como criterio MVP.
- Pacientes inactivos permanecen visibles para trazabilidad y para preservar citas históricas.

Exclusiones preservadas: historia clínica, datos clínicos, consentimientos, adjuntos, diagnósticos, fusión/deduplicación avanzada, validación externa de documentos, contactos múltiples y creación automática de perfiles de pagador. No se expone `schema_name` ni se piden UUIDs manualmente al admin.

### Fase 6B.13 — Citas virtuales derivadas desde sede

En Citas, la UI no muestra selector libre de modalidad. La sede seleccionada define si la cita es virtual o presencial mediante `locations.is_virtual`.

- Sede virtual: se muestra un área “Cita virtual”, se deshabilita consultorio y se muestran campos de link manual. Solo una URL de reunión permite considerar el link creado o enviado; ID y código de acceso son auxiliares.
- Sede presencial: se muestra un área “Cita presencial”, se conserva consultorio y se ocultan campos de link virtual.

El frontend no envía `modality` en creación de citas.
