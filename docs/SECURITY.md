# SECURITY.md  
# Seguridad, Privacidad y Auditoría

## 1. Principios

TotalChat manejará datos personales administrativos.

No manejará historia clínica en el MVP.

## 2. Secretos

No guardar secretos en repositorio.

Usar variables de entorno:

- OPENAI_API_KEY.
- DATABASE_URL.
- REDIS_URL.
- TELEGRAM_BOT_TOKEN.
- JWT_SECRET.
- WOMPI_KEYS futuras.

## 3. Autenticación admin

Recomendado:

- Email/password.
- Password hash Argon2 o bcrypt.
- JWT access token.
- Refresh token.
- Roles por tenant.


## 4.0. Provisioning operativo de tenants (Fase 6C.1.1)

El alta operativa de tenants antes del login real se realiza mediante `python3 -m app.tenancy.create_tenant`. El comando solo acepta `--name` y `--slug`, genera `schema_name` internamente, valida el schema seguro derivado, escribe en `public.tenants`, crea el schema tenant y aplica migraciones idempotentes. No acepta ni muestra `schema_name`, no crea owner automáticamente, no expone endpoint HTTP, no implementa signup y no reactiva tenants inactivos.


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

## 4. Autorización

Roles:

```text
owner
admin
staff
readonly
```

Toda acción administrativa debe validar tenant y rol.

## 5. Multi-tenancy

Reglas:

- Resolver tenant antes de acceder a datos.
- Usar schema del tenant.
- No permitir que LLM elija schema.
- No ejecutar herramientas sin contexto tenant.
- Tests de aislamiento obligatorios.

## 6. Webhooks

Telegram y futuros canales deben validar:

- Token/secreto.
- Origen si aplica.
- Payload esperado.
- Tenant channel activo.

## 7. Auditoría

Auditar:

- Login.
- Cambios de contraseña.
- Creación y cambios de usuarios.
- Cambios de roles.
- Cambios de servicios.
- Cambios de precios.
- Cambios de disponibilidad.
- Creación/cancelación/reprogramación de citas.
- Aprobación/rechazo de pagos.
- Actualización de links virtuales.
- Cambios de configuración de pago.

## 8. Datos personales

Minimizar datos.

No pedir datos no necesarios al inicio.

Permitir perfiles incompletos.

## 9. Pagos

Transferencias requieren revisión humana.

La evidencia visual no confirma pago.

## 10. Citas virtuales

Links de reunión deben tratarse como datos sensibles operativos.

Solo usuarios autorizados pueden modificarlos.

## 11. Logs

Evitar loguear secretos.

Evitar loguear información sensible innecesaria.

## 12. Backups

Pendiente definir estrategia exacta.

Debe considerar:

- Backup completo.
- Restauración por tenant.
- Export por schema.

## 3.1. Fase 6C.2 — JWT administrativo real

La consola admin usa login email/password contra `public.users`. Solo usuarios `active`, con password bcrypt válido, vínculo activo en `public.user_tenants` y tenant activo pueden recibir JWT. El secret obligatorio es `TOTALCHAT_JWT_SECRET`; si no está definido, la emisión o validación del token falla de forma explícita.

El access token dura 30 minutos (`expires_in = 1800`) e incluye únicamente `sub`, `email`, `exp` y tipo `access`. No incluye `schema_name`, password hash ni datos tenant sensibles. Refresh tokens, recuperación de contraseña, OAuth, invitaciones y gestión UI de usuarios quedan fuera de Fase 6C.2.

Todas las rutas `/api/admin/*` requieren `Authorization: Bearer <token>` y `X-TotalChat-Tenant-Id`. El header de tenant solo selecciona entre tenants autorizados; no es fuente de autorización por sí solo.
