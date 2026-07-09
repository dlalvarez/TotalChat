# PAYMENTS.md  
# Modelo de Pagos Manuales, Simulados, Evidencias y Revisión Manual

## 1. Principios

TotalChat soporta en el MVP backend solo métodos manuales/simulados, sin pasarela real:

- `transfer`: transferencia manual con evidencia y revisión administrativa.
- `simulated`: pago simulado para MVP/testing.
- `pay_on_site`: pago en sitio configurable por tenant.

Wompi, tarjetas, conciliación bancaria automática y gateways reales son futuros y no forman parte del baseline actual.

## 2. Regla principal

Una transferencia no debe confirmar automáticamente una cita solo por recibir una imagen, PDF o captura.

La IA puede prevalidar el comprobante o extraer datos, pero no confirmar recepción real del dinero ni aprobar pagos.

## 3. Métodos

### 3.1. Transferencia manual

Flujo:

```text
Paciente elige transfer
↓
Sistema muestra instrucciones
↓
PaymentAttempt queda evidence_required
↓
Paciente tiene evidence_deadline_minutes para enviar evidencia
↓
Si no envía evidencia:
    PaymentAttempt queda expired
    slot se libera solo si release_slot_on_missing_evidence=true
↓
Si envía evidencia:
    PaymentAttempt queda evidence_received
    cita queda en revisión manual de pago
    slot queda protegido
↓
IA puede prevalidar sin aprobar
↓
Admin revisa
↓
Admin aprueba o rechaza
```

### 3.2. Pago simulado

`simulated` existe para MVP/testing.

Reglas:

- Debe quedar distinguible de una transferencia aprobada o una pasarela real futura.
- Puede producir `simulated_approved`.
- No representa confirmación bancaria.
- Debe preservar historial de booking/payment.

### 3.3. Pago en sitio

Debe ser configurable con `allow_pay_on_site`.

Si el tenant no acepta pago en sitio, no se ofrece.

Si se acepta, la cita puede quedar confirmada bajo política de pago en sitio, sin afirmar pago remoto ni confirmación bancaria.

## 4. Evidencia de transferencia

El sistema debe permitir recibir evidencia como:

- Imagen.
- PDF.
- Captura.
- Archivo.

Campos implementados/conceptuales alineados:

```text
storage_object_key
original_filename
content_type
uploaded_at
uploaded_channel
notes
```

La IA puede extraer:

- Valor.
- Fecha.
- Cuenta destino.
- Referencia.
- Banco.
- Nombre visible.
- Posibles inconsistencias.

Pero debe advertir que la imagen puede ser falsa o manipulada. Evidencia recibida protege el slot, pero nunca aprueba el pago por sí sola.

## 5. Revisión manual

La revisión administrativa debe permitir:

- Ver paciente, cita, profesional, servicio, fecha y valor esperado.
- Ver evidencia.
- Ver resultado de prevalidación IA si existe.
- Aprobar.
- Rechazar.
- Registrar notas.

Debe auditar:

```text
payment_attempt_id
decision
reviewer_user_id
reviewed_at
notes
```

`confirmed_against_bank` puede agregarse en una fase futura de endurecimiento, pero no es requisito bloqueante del MVP manual/simulado actual salvo que una spec futura lo exija.

## 6. Revisión vencida

Cuando el paciente envió evidencia, el horario queda protegido.

Si la revisión vence:

- No liberar automáticamente por defecto.
- Marcar o señalar revisión vencida mediante el flujo interno `mark-review-overdue`.
- Alertar al administrador o escalar mediante automatización complementaria si existe.
- Liberar slot solo si `release_slot_on_review_overdue=true`.

Esto evita castigar al paciente por falta de gestión administrativa.

## 7. No evidencia

Si el paciente no envía evidencia dentro del plazo:

- `PaymentAttempt` puede pasar a `expired` mediante `expire-missing-evidence`.
- El slot se libera solo según `release_slot_on_missing_evidence`.
- Se puede notificar al paciente mediante canales o n8n complementario.

## 8. Políticas por tenant

Cada tenant puede configurar:

```text
allow_transfer
allow_simulated_payment
allow_pay_on_site
evidence_deadline_minutes
manual_review_deadline_minutes
release_slot_on_missing_evidence
release_slot_on_review_overdue
```

Valores recomendados:

```text
allow_transfer = true
allow_simulated_payment = true
allow_pay_on_site = false
release_slot_on_missing_evidence = true
release_slot_on_review_overdue = false
```

## 9. Reembolsos y pasarelas futuras

Reembolsos, Wompi, tarjetas, webhooks de pasarela, conciliación bancaria y confirmación automática por gateway quedan para fases futuras explícitas.
