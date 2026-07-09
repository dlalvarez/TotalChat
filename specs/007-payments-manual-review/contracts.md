# Contracts — Spec 007 Manual and Simulated Payments

This document proposes API contracts for later implementation of manual and simulated payments. It follows the API surface conventions in `docs/API_CONTRACTS.md` and is documentation only.

No endpoint in this document is implemented by the specification PR.

## 1. Admin contracts

Admin routes require authenticated administrative access and resolved tenant context. Clients must not provide database schema names.

### 1.1. `POST /api/admin/payment-settings`

Purpose: create tenant or organization-scoped payment settings.

Suggested request fields:

- `organization_id`, if implementation scopes settings to organization rather than tenant.
- `allow_transfer`.
- `allow_simulated_payment`.
- `allow_pay_on_site`.
- `evidence_deadline_minutes`.
- `manual_review_deadline_minutes` or review policy fields.
- `release_slot_on_missing_evidence`.
- `release_slot_on_review_overdue`, default `false`.
- `status`.

Suggested response: created payment settings resource.

### 1.2. `GET /api/admin/payment-settings`

Purpose: read effective tenant or organization-scoped payment settings.

Suggested query parameters:

- `organization_id`, if implementation supports organization-scoped settings.
- `status`.

Suggested response: payment settings resource or list, depending on selected scope.

### 1.3. `PATCH /api/admin/payment-settings`

Purpose: update payment settings without changing payment attempt history.

Suggested request fields:

- Any configurable field from `payment_settings`.

Rules:

- Updating settings must not rewrite previous payment attempt deadlines or review decisions unless a later implementation explicitly defines a safe recalculation policy.
- `release_slot_on_review_overdue` must default to `false`.

### 1.4. `GET /api/admin/payment-attempts`

Purpose: list payment attempts for administrative review and audit.

Suggested query parameters:

- `booking_id`.
- `method`.
- `status`.
- `from`.
- `to`.
- `review_overdue`.

Suggested response fields:

- Payment attempt fields.
- Booking reference.
- Evidence summary.
- Latest review summary, if present.

### 1.5. `POST /api/admin/payment-attempts/{payment_attempt_id}/approve`

Purpose: explicitly approve a payment attempt through administrative action.

Suggested request fields:

- `notes`, optional.
- `confirmed_against_bank`, optional for future manual policies, but not an automatic bank reconciliation signal.

Rules:

- AI cannot call this endpoint as an approval authority.
- Approval must record reviewer identity when available.
- Approval must transition booking state through domain services.
- Simulated payments must not be represented as real bank confirmation.

### 1.6. `POST /api/admin/payment-attempts/{payment_attempt_id}/reject`

Purpose: explicitly reject a payment attempt through administrative action.

Suggested request fields:

- `notes`, required or recommended by implementation policy.
- `reason`, optional structured reason.

Rules:

- Rejection must record reviewer identity when available.
- Rejection must transition booking/payment state through domain services.
- Rejection must preserve evidence and review audit history.

### 1.7. `GET /api/admin/payment-reviews`

Purpose: list payment review decisions and pending/overdue review work.

Suggested query parameters:

- `payment_attempt_id`.
- `decision`.
- `reviewer_user_id`.
- `from`.
- `to`.
- `overdue`.

Suggested response fields:

- Payment review fields.
- Payment attempt summary.
- Booking reference.

## 2. Public or channel-facing contracts for later phases

### 2.1. `POST /api/public/bookings/{booking_id}/payment-evidence`

Purpose: register payment evidence for a booking in transfer/manual flow.

Suggested request fields:

- `payment_attempt_id`, if not inferred from active booking attempt.
- `file` or file reference placeholder.
- `original_filename`.
- `content_type`.
- `uploaded_channel`.
- `notes`, optional.

Rules:

- Evidence registration does not approve payment.
- Evidence registration moves the attempt toward manual review.
- Evidence received protects the slot while review is pending.
- The endpoint must not accept card data, bank credentials, or bank secrets.

## 3. Internal contracts

Internal routes are intended for workers, schedulers, or controlled automation and must be protected by an internal token or equivalent mechanism.

### 3.1. `POST /api/internal/payment-attempts/{payment_attempt_id}/mark-overdue`

Purpose: mark a manual review as overdue when the review target deadline is missed.

Rules:

- Marking review overdue must not release the slot by default.
- The action should create alert/escalation expectations for administrators.
- Any slot release on review overdue requires explicit tenant configuration.

### 3.2. `POST /api/internal/payment-attempts/{payment_attempt_id}/expire-missing-evidence`

Purpose: expire a transfer/manual payment attempt when evidence is missing after the configured deadline.

Rules:

- Missing evidence can expire/release the booking only according to tenant policy.
- Expiry must be performed by backend-owned domain services.
- Expiry must preserve audit history.

## 4. Contract guardrails

- Follow `docs/API_CONTRACTS.md` response and error conventions.
- Use UUIDs for primary identifiers.
- Resolve tenant context on the backend.
- Do not expose schema names to clients, channels, or LLMs.
- Support idempotency for critical actions where appropriate.
- Do not implement Wompi, credit cards, real gateways, bank reconciliation, Telegram changes, WhatsApp, LangGraph changes, frontend admin, n8n automations, or external scheduling providers in this phase.
