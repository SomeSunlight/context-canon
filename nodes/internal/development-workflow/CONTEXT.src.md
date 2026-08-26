# ContextCanon Development Workflow — Local Context Source
<!-- ctx:node id="c4c94726-3cc7-4df6-b779-72bbf9c06f40" version="0.1.0-draft" -->

## Overview

Internal dogfood context for carrying ContextCanon development safely across long LLM-assisted sessions, tool failures, and human review rounds. It is internal first; promote it to the reusable Node Library only after real cross-project use proves the method generic.

## Rules

### Recoverable planning

- **Plan a coherent change block before editing:** Before starting a new coherent ContextCanon development block, add a short purpose and checklist to `PLAN.md`.
  Why: Repository state must explain what work is in progress even if the chat, model session, or tool run disappears.
  <!-- ctx:rule id="CCW-001" -->

- **Checkpoint completed plan items immediately:** When a listed step is actually complete, mark its `PLAN.md` checkbox `[x]` immediately rather than reconstructing completion at the end of a long session.
  Why: Immediate checkpoints turn PLAN into a reliable recovery ledger instead of requiring plan archaeology after an interruption.
  <!-- ctx:rule id="CCW-002" -->

- **Keep recovery-critical knowledge in the repository:** Put decisions, active constraints, accepted state, and next steps needed to resume work in repository documentation rather than relying on chat history or model memory.
  Why: Long conversations and agent sessions are transient; the repository is the durable shared recovery point for humans and tools.
  <!-- ctx:rule id="CCW-003" -->

### Proportional verification

- **Batch related edits before dogfood regeneration:** For one coherent correction block, make the related authoring/code changes and run deterministic tests first; use one compiler-reported drift result to regenerate dogfood once near the review boundary instead of regenerating after every micro-edit.
  Why: Generated-output verification is valuable, but repeating the full materialization cycle after every tiny edit adds ceremony without increasing confidence in superseded intermediate heads.
  <!-- ctx:rule id="CCW-004" -->

- **Require exact-head green verification before review completion:** Before presenting a development block as review-ready or merging it, require the exact current head to pass the deterministic test suite and `contextcanon check --all .` with zero generated drift.
  Why: Batching intermediate work is safe only when the final review object is fully reproducible and verified.
  <!-- ctx:rule id="CCW-005" -->

### Human review gate

- **Do not merge without explicit project-owner approval:** Keep a review PR open until the project owner explicitly approves the reviewed result.
  Why: Green CI proves deterministic consistency, not that the product or documentation is acceptable to its human reviewer.
  <!-- ctx:rule id="CCW-006" -->

## Topics

### Executing a development block

When planning, resuming, checkpointing, testing, dogfooding, or preparing a ContextCanon change block for project-owner review:

Required:
- Resource: `docs/change-workflow.md`
<!-- ctx:topic id="CCW-TOPIC-CHANGE-WORKFLOW" -->
