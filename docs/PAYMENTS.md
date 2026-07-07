# PAYMENTS.md  
# Modelo de Pagos, Transferencias, Evidencias y Revisión Manual

## 1. Principios

TotalChat debe soportar varios métodos de pago, pero cada uno tiene reglas distintas.

Métodos iniciales:

- Pago simulado.
- Transferencia manual.
- Pago en sitio.
- Pasarela futura Wompi.

## 2. Regla principal

Una transferencia no debe confirmar automáticamente una cita solo por recibir una imagen.

La IA puede prevalidar el comprobante, pero no confirmar recepción real del dinero.

## 3. Métodos

### 3.1. Pasarela

Cuando se implemente Wompi:

- Se genera link.
- Paciente paga.
- Wompi envía webhook.
- Backend valida.
- Pago pasa a `paid`.
- Cita pasa a `confirmed`.

### 3.2. Transferencia manual

Flujo:

```text
Paciente elige transferencia
↓
Sistema muestra instrucciones
↓
Cita queda pending_payment_evidence
↓
Paciente tiene X minutos configurables para enviar evidencia
↓
Si no envía evidencia:
    reserva expira
    slot se libera
↓
Si envía evidencia:
    cita queda pending_manual_payment_review
    slot queda protegido
↓
IA prevalida
↓
Admin revisa contra cuenta bancaria
↓
Admin aprueba o rechaza
```

### 3.3. Pago en sitio

Debe ser configurable.

Si el tenant no acepta pago en sitio, no se ofrece.

Si se acepta:

```text
booking = confirmed_without_payment
payment_status = pay_at_location
```

## 4. Evidencia de transferencia

El sistema debe permitir recibir evidencia:

- Imagen.
- PDF.
- Captura.
- Archivo.

La IA puede extraer:

- Valor.
- Fecha.
- Cuenta destino.
- Referencia.
- Banco.
- Nombre visible.
- Posibles inconsistencias.

Pero debe advertir que la imagen puede ser falsa o manipulada.

## 5. Revisión manual

Pantalla administrativa:

- Paciente.
- Cita.
- Profesional.
- Servicio.
- Fecha.
- Valor esperado.
- Evidencia.
- Resultado IA.
- Botón aprobar.
- Botón rechazar.
- Botón solicitar nueva evidencia.
- Campo notas.
- Confirmación de revisión contra banco.

Debe auditar:

- reviewed_by.
- reviewed_at.
- decision.
- notes.
- confirmed_against_bank.

## 6. Revisión vencida

Cuando el paciente envió evidencia, el horario queda protegido.

Si la revisión vence:

- No liberar automáticamente.
- Marcar `review_overdue`.
- Alertar al administrador.
- Escalar según configuración.

Esto evita castigar al paciente por falta de gestión administrativa.

## 7. No evidencia

Si el paciente no envía evidencia dentro del plazo:

- Expira reserva.
- Libera slot.
- Notifica al paciente.

## 8. Políticas por tenant

Cada tenant puede configurar:

- allow_gateway_payment.
- allow_manual_transfer.
- allow_pay_at_location.
- require_payment_before_confirmation.
- payment_evidence_due_minutes.
- manual_review_due_policy.
- manual_review_due_time.
- auto_expire_if_no_evidence.
- auto_expire_if_review_overdue.
- refund_policy_days.

Valores recomendados:

```text
auto_expire_if_no_evidence = true
auto_expire_if_review_overdue = false
require_manual_review_for_transfers = true
```

## 9. Reembolsos

Si un paciente cancela y ya pagó, el sistema debe manejar reembolso según política del tenant.

El mensaje de cancelación debe informar:

- Que el cupo será liberado.
- Que una nueva reserva depende de disponibilidad.
- Que el reembolso se gestiona en X días configurables.
