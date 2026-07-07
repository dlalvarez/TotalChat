# Codex instructions for TotalChat

TotalChat is governed by a strict, lightweight Specification Driven Development (SDD) process. Codex Cloud is an implementation executor, not a product planner or architecture authority.

## Required reading before changes

Before making repository changes, always read:

1. `docs/CONSTITUTION.md`
2. `docs/ROADMAP.md`
3. `docs/DECISIONS.md`
4. The relevant spec folder under `specs/`
5. Any relevant supporting governance/domain document under `docs/`

## Scope and sequencing rules

- Follow `docs/ROADMAP.md`, `docs/DECISIONS.md`, and the relevant `specs/` documents exactly.
- Do not mix phases in a single implementation.
- Do not implement future phases early.
- Do not modify roadmap, governance, decisions, architecture, or specs unless the user explicitly instructs you to do so.
- If scope is ambiguous, choose the minimal implementation compatible with the current spec and document the limitation in the PR or final response.
- If implementation requires deviating from documented scope, stop and request/record an accepted deviation before implementing it.

## Product constraints

- Do not turn n8n into core business logic. n8n may only be complementary automation around backend-owned domain logic.
- Do not implement WhatsApp before Telegram.
- Do not implement Wompi before simulated payments.
- Do not implement booking before the multitenancy and database foundation are implemented.
- Do not let LLMs, channels, or automations become the source of truth for tenant, booking, payment, or medical data.

## Implementation discipline

- Keep changes focused on the requested spec and phase.
- Prefer small, auditable changes with explicit exclusions.
- Run `python scripts/check_sdd_scope.py` and relevant tests before committing.
