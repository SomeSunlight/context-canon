# State and Planning

ContextCanon separates current project reality from inherited governance.

## STATE.md

`STATE.md` is optional framework-aware project state, written for humans and agents.

It can record:

- current development focus,
- known gaps,
- transitional architecture,
- temporary constraints,
- where active planning lives.

State is local to the project and is never inherited by child nodes as governance.

State also does not change the semantic version of a node's published context merely because project progress changed.

## PLAN.md or another planning system

ContextCanon does not prescribe project management methodology.

A project may use `PLAN.md`, GitHub Issues, Jira, Logseq, or another planning system. `STATE.md` can point to the authoritative location.

For small projects, a Markdown checklist is sufficient and deliberately transparent.

## Standard repository documents

The intended information split is:

- `README.md` — what the project is and how to start,
- `CONTRIBUTING.md` — how to change it,
- `CHANGELOG.md` — notable completed/released changes,
- `STATE.md` — what is true about the project right now,
- planning system — intended future work,
- `CONTEXT.src.md` — local editable context delta,
- `CONTEXT.md` — compact generated official entry,
- `CONTEXT/` — deeper generated/materialized package resources.

State and planning are deliberately outside the inherited Official Context Package unless a project explicitly references some stable document as context material.
