---
name: Phase implementation
about: Track implementation work for one documented SDD phase/spec
title: "Phase: <phase/spec name>"
labels: ["phase", "sdd"]
assignees: ""
---

## Governance references

- Constitution: `docs/CONSTITUTION.md`
- Roadmap phase: `docs/ROADMAP.md#...`
- Decisions: `docs/DECISIONS.md`
- Spec path: `specs/...`

## Phase objective

Describe the documented objective for this phase without expanding scope:


## Included scope

- 

## Explicitly excluded scope

- 

## Dependencies / sequencing

List prior phases or specs that must already be complete:

- 

## Acceptance criteria

- [ ] Implementation matches the referenced spec.
- [ ] No future phase is implemented early.
- [ ] Tests are added or updated for included scope.
- [ ] `python scripts/check_sdd_scope.py` passes.
- [ ] `cd backend && pytest` passes.
