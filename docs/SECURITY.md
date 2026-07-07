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
