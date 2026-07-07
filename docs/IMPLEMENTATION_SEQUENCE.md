# Implementation Sequence

TotalChat implementation must follow the documented roadmap and specs in order. This document summarizes sequencing constraints for implementers and automation agents.

## Required sequence

1. Governance and SDD documentation baseline.
2. Technical foundation baseline.
3. Multitenancy and database foundation.
4. Booking domain model.
5. Scheduling and reservations without AI.
6. Conversational agent and channel integrations according to the roadmap.
7. Payments according to the roadmap and accepted decisions.

## Guardrails

- Do not implement multitenancy, database models, reservations, Telegram, LangGraph, or payments before their documented phase is explicitly in scope.
- Do not implement WhatsApp before Telegram.
- Do not implement Wompi before simulated payments.
- Do not implement booking before multitenancy and database foundation.
- Use `docs/ACCEPTED_DEVIATIONS.md` to record approved exceptions before implementation.
