# Spec 007 — Manual and Simulated Payments

## 1. Purpose

Define the manual and simulated payment baseline for TotalChat/MediChat before any real payment gateway is introduced.

This specification documents the domain language, proposed state model, data model expectations, booking interactions, audit expectations, and acceptance criteria for later implementation PRs in Fase 5 — Pagos manuales/simulados.

This PR is documentation/specification only. It does not implement code, database migrations, API endpoints, frontend screens, channel behavior, payment gateways, Wompi, or automations.


## 1.1. Implementation status

Backend baseline for this specification has been implemented and lightly validated through PR #20–#26, including validation against real PostgreSQL schema-per-tenant. PR #26 fixed tenant-scoped transaction ordering around `SET LOCAL search_path`. This note records implementation status only and does not expand or change the business scope of Spec 007.

## 2. In scope

This specification covers only the following payment baseline capabilities:

- `payment_settings`.
- `payment_attempts`.
- `payment_evidence`.
- `payment_reviews`.
- Transfer/manual payment flow.
- Simulated payment flow.
- Tenant-configurable pay-on-site flow.
- Evidence upload/registration expectations.
- Manual administrative review.
- Evidence deadline.
- Review target deadline.
- Review overdue behavior.
- Booking state interactions.
- Audit expectations.
- API contract proposal.
- Acceptance criteria.
- Implementation tasks for later PRs.

## 3. Out of scope

The following are explicitly excluded from this phase and must not be implemented under this specification:

- Wompi.
- Real payment gateway integrations.
- Credit card processing.
- Bank API reconciliation.
- Automatic approval against bank movement.
- Refunds automation.
- WhatsApp.
- Telegram changes.
- LangGraph changes.
- Frontend admin implementation.
- Campaigns.
- n8n automation implementation.
- External scheduling providers.
- Changing booking availability logic.
- Medical or clinical data.

## 4. Business rules

### 4.1. Transfer/manual payment

- If the patient chooses transfer, the booking may move to a payment-pending state while the system waits for payment evidence.
- The tenant must configure how long the system waits for evidence.
- If evidence is not received within the configured time, the booking may expire and release the slot according to tenant policy.
- If evidence is received, the booking moves to manual administrative review and the slot remains protected.
- Manual approval or rejection must be an administrative action.
- Evidence alone must never confirm payment automatically.

### 4.2. Review deadlines and overdue behavior

- Lack of timely admin review must not automatically release the slot unless an explicit tenant configuration allows it.
- Review overdue should generate an overdue state, alert, or escalation expectation, not punish the patient.
- Review may have a target deadline such as next business day by noon, represented as configurable policy fields or derived deadline minutes in implementation.
- `release_slot_on_review_overdue` must default to `false` if implemented.

### 4.3. Simulated payments

- Simulated payments are for MVP/testing only.
- Simulated approval must not be represented as real bank confirmation.
- Simulated payment records must be visibly distinguishable from real gateway or manual bank-confirmed payments.
- Simulated payment behavior must preserve booking and payment audit history.

### 4.4. Pay on site

- Pay-on-site must be tenant-configurable.
- If tenant policy allows it, a booking may become `confirmed_without_payment`.
- Pay-on-site must not imply remote payment collection, bank confirmation, gateway confirmation, or card processing.

### 4.5. AI and automation boundaries

- The system must never let the AI approve payments.
- The system must never let the LLM invent payment status.
- LLMs, channels, and automations must not become the source of truth for payment state.
- Payment state changes must be executed through backend-owned domain services in later implementation PRs.

### 4.6. Audit and source of truth

- PostgreSQL remains the source of truth for payment settings, attempts, evidence, reviews, and booking/payment state.
- The system must preserve booking/payment audit history.
- Administrative decisions must record reviewer identity when available, decision, timestamp, and notes.
- Payment data must not store real card secrets, bank credentials, or bank API secrets.

## 5. Suggested state model

These statuses are proposed for later implementation. They are not implemented by this specification PR.

### 5.1. Booking/payment interaction states

- `pending_payment`: booking is waiting for a payment decision or method-specific next step.
- `pending_payment_evidence`: transfer/manual flow is waiting for patient evidence before the configured evidence deadline.
- `pending_manual_payment_review`: evidence was received and an administrator must approve or reject it.
- `review_overdue`: evidence was received but the administrative review target deadline was missed.
- `confirmed`: booking is confirmed after successful allowed payment or explicit administrative approval.
- `confirmed_without_payment`: booking is confirmed under tenant pay-on-site policy.
- `cancelled` or `expired`: booking was cancelled or expired due to missing evidence only when tenant policy allows slot release.

### 5.2. Payment attempt statuses

- `pending`: payment attempt was created and is awaiting method-specific progression.
- `evidence_required`: transfer/manual attempt requires evidence before the evidence deadline.
- `evidence_received`: evidence has been registered.
- `under_review`: evidence is awaiting manual administrative review.
- `approved`: administrator approved the payment attempt.
- `rejected`: administrator rejected the payment attempt.
- `expired`: attempt expired due to missing evidence or another explicit expiry policy.
- `cancelled`: attempt was cancelled by a valid domain action.
- `simulated_approved`: simulated payment was approved for MVP/testing and is not real bank confirmation.

### 5.3. Payment methods

- `transfer`: manual transfer flow requiring evidence and administrative review.
- `simulated`: MVP/testing flow without real money movement.
- `pay_on_site`: tenant-configurable policy that may confirm without prior payment.

## 6. Suggested data model

The following entities and fields are proposed at specification level only.

### 6.1. `payment_settings`

- `id`.
- `organization_id` or tenant scope depending on the existing architecture chosen during implementation.
- `allow_transfer`.
- `allow_simulated_payment`.
- `allow_pay_on_site`.
- `evidence_deadline_minutes`.
- `manual_review_deadline_minutes` or review policy fields.
- `release_slot_on_missing_evidence`.
- `release_slot_on_review_overdue`, default `false`.
- `created_at`.
- `updated_at`.
- `status`.

### 6.2. `payment_attempts`

- `id`.
- `booking_id`.
- `method`.
- `amount`.
- `currency`.
- `status`.
- `expires_at`.
- `evidence_received_at`.
- `reviewed_at`.
- `reviewed_by_user_id`, nullable.
- `created_at`.
- `updated_at`.

### 6.3. `payment_evidence`

- `id`.
- `payment_attempt_id`.
- `storage_object_key` or file reference placeholder.
- `original_filename`.
- `content_type`.
- `uploaded_at`.
- `uploaded_channel`.
- `notes`.

### 6.4. `payment_reviews`

- `id`.
- `payment_attempt_id`.
- `decision`.
- `reviewer_user_id`, nullable.
- `reviewed_at`.
- `notes`.
- `created_at`.

## 7. Booking interactions

- Booking state transitions must remain controlled by booking/payment domain services in later implementation PRs.
- Payment implementation must not bypass availability or booking domain invariants.
- Evidence received protects the slot while review is pending.
- Missing evidence may release the slot only according to explicit tenant policy.
- Review overdue does not release the slot by default.
- Rejection behavior must be handled by explicit domain policy in implementation and must preserve audit history.

## 8. Acceptance criteria for later implementation PRs

- Settings can configure transfer, simulated payment, and pay-on-site options.
- Transfer flow protects the slot after evidence is received.
- Missing evidence can expire according to tenant policy.
- Review overdue does not release the slot by default.
- Admin review approval and rejection are explicit actions.
- AI cannot approve payment.
- Booking state transitions remain through domain services.
- Payment data never stores real card or bank secrets.
- Wompi remains out of scope.
- Simulated payments are distinguishable from real bank or gateway confirmation.
- Payment attempts, evidence, and reviews preserve audit history.
