# Tasks — Spec 007 Manual and Simulated Payments

This task breakdown is a planned implementation sequence for future PRs. These tasks are not implemented by PR #19.

## PR 20 — Payment data model and tenant migrations

- [ ] Add tenant-scoped `payment_settings` data model.
- [ ] Add tenant-scoped `payment_attempts` data model.
- [ ] Add tenant-scoped `payment_evidence` data model.
- [ ] Add tenant-scoped `payment_reviews` data model.
- [ ] Add status/method enums or validated constants.
- [ ] Add timestamps, status fields, indexes, and audit-friendly fields.
- [ ] Ensure no real card or bank secrets are stored.
- [ ] Run SDD scope check and relevant migration/model tests.

## PR 21 — Admin payment settings endpoints

- [ ] Implement `POST /api/admin/payment-settings`.
- [ ] Implement `GET /api/admin/payment-settings`.
- [ ] Implement `PATCH /api/admin/payment-settings`.
- [ ] Enforce tenant context and admin authorization.
- [ ] Default `release_slot_on_review_overdue` to `false`.
- [ ] Add tests for settings validation and tenant isolation.

## PR 22 — Payment attempt creation and simulated payment baseline

- [ ] Add domain service for creating payment attempts through backend-owned logic.
- [ ] Support `transfer`, `simulated`, and `pay_on_site` methods according to settings.
- [ ] Implement simulated payment baseline as MVP/testing behavior only.
- [ ] Ensure simulated approval is distinguishable from real bank confirmation.
- [ ] Ensure booking state changes go through domain services.
- [ ] Add tests for method availability and simulated payment behavior.

## PR 23 — Transfer evidence registration baseline

- [ ] Implement evidence registration for transfer/manual payment attempts.
- [ ] Implement `POST /api/public/bookings/{booking_id}/payment-evidence` or the approved channel-facing equivalent.
- [ ] Move attempts from evidence-required state to manual review state when evidence is received.
- [ ] Protect the booking slot after evidence is received.
- [ ] Preserve evidence metadata and audit history.
- [ ] Add tests for missing evidence, received evidence, and tenant isolation.

## PR 24 — Manual payment review actions

- [ ] Implement `GET /api/admin/payment-attempts`.
- [ ] Implement `POST /api/admin/payment-attempts/{payment_attempt_id}/approve`.
- [ ] Implement `POST /api/admin/payment-attempts/{payment_attempt_id}/reject`.
- [ ] Implement `GET /api/admin/payment-reviews`.
- [ ] Record reviewer identity when available, decision, timestamp, and notes.
- [ ] Ensure AI cannot approve payments.
- [ ] Ensure approval/rejection transitions booking/payment state through domain services.
- [ ] Add tests for approval, rejection, authorization, and audit history.

## PR 25 — Expiry and review-overdue domain services

- [ ] Implement missing-evidence expiry service.
- [ ] Implement `POST /api/internal/payment-attempts/{payment_attempt_id}/expire-missing-evidence`.
- [ ] Implement review-overdue service.
- [ ] Implement `POST /api/internal/payment-attempts/{payment_attempt_id}/mark-overdue`.
- [ ] Ensure missing evidence can release the slot only according to tenant policy.
- [ ] Ensure review overdue does not release the slot by default.
- [ ] Add tests for evidence deadline, review target deadline, overdue behavior, and audit history.
