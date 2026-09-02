# Development Workflow — Local Context Source
<!-- ctx:node id="c4c94726-3cc7-4df6-b779-72bbf9c06f40" version="0.2.0-draft" -->

## Overview

Reusable workflow for carrying project development safely across long human/LLM-assisted sessions, tool failures, review rounds, and merges. It standardizes recoverable planning and review boundaries without prescribing a particular programming language, CI system, operating system, or ContextCanon baseline.

This Node deliberately does **not** compose ContextCanon Foundation. A consumer may compose Foundation and this workflow independently when both are useful; using the workflow alone must not pull unrelated framework governance transitively.

## Rules

### Recoverable planning

- **Plan a coherent change block before editing:** Before starting a new coherent development block, record a short purpose and checklist in the project's durable planning surface; use `PLAN.md` when the project follows this workflow convention.
  Why: Repository state must explain what work is in progress even if the chat, model session, or tool run disappears.
  <!-- ctx:rule id="CCW-001" -->

- **Checkpoint completed plan items immediately:** When a listed step is actually complete, mark its `PLAN.md` checkbox `[x]` immediately rather than reconstructing completion at the end of a long session.
  Why: Immediate checkpoints turn PLAN into a reliable recovery ledger instead of requiring plan archaeology after an interruption.
  <!-- ctx:rule id="CCW-002" -->

- **Keep recovery-critical knowledge in the repository:** Put decisions, active constraints, accepted state, and next steps needed to resume work in repository documentation such as `PLAN.md`, `STATE.md`, or the project's equivalent rather than relying on chat history or model memory.
  Why: Long conversations and agent sessions are transient; the repository is the durable shared recovery point for humans and tools.
  <!-- ctx:rule id="CCW-003" -->

- **Resume recent explicit continuation without re-proving unchanged state:** When the project owner resumes work after a short conversational interruption, explicitly says to continue, and reports no intervening repository changes, continue from the last established branch/PR state unless a repository operation gives evidence that it changed. Do not spend a new work cycle re-checking already established repository facts merely to prove that nothing happened.
  Why: In a controlled single-owner workflow, repeated defensive re-verification consumes the useful working window without adding evidence. Any stated or observed intervening change still invalidates this assumption.
  <!-- ctx:rule id="CCW-007" -->

### Proportional verification

- **Batch related edits before expensive final verification:** For one coherent correction block, make the related authoring/code changes and run proportionate focused checks first; do not repeat the project's most expensive generated-output, integration, packaging, or full verification cycle after every micro-edit.
  Why: Final verification is valuable, but repeating it on superseded intermediate heads adds ceremony without increasing confidence in the candidate that will actually be reviewed or merged.
  <!-- ctx:rule id="CCW-004" -->

- **Use owner-approved fast-run blocks without weakening the final gate:** When the project owner explicitly approves a coherent implementation scope and says intermediate product review is unnecessary, mark the fast-run as active in the durable PLAN with its scope and exit condition, keep recovery checkpoints and focused verification inside bounded work blocks, and defer repeated PR-description polish, full CI, generated-output regeneration, and other review ceremony until the coherent review candidate. When the fast-run ends, record that closure before returning to ordinary review cadence.
  Why: Explicit delegation can remove intermediate coordination cost without sacrificing recoverability. Visible start/scope/exit/closure boundaries prevent a long single-worker fast-run from becoming undocumented process state, while final human review and exact-head merge verification remain unchanged.
  <!-- ctx:rule id="CCW-009" -->

- **Require exact-head green verification at the merge gate, not the first review gate:** A coherent development block may be presented for project-owner review while understood and disclosed CI failures or generated drift remain. After explicit project-owner approval and before merging, require the exact current head to pass the project's complete merge-gate verification, including zero generated drift when generated canonical output is part of the project contract.
  Why: Human review should happen before spending finalization effort on a candidate that may still change, while the accepted branch remains protected by a strict reproducibility gate.
  <!-- ctx:rule id="CCW-005" -->

### Human review gate

- **Do not merge without explicit project-owner approval:** Keep a review PR or equivalent change set open until the project owner explicitly approves the reviewed result.
  Why: Green automation proves only the properties it checks; it does not prove that the product, architecture, or documentation is acceptable to its human owner.
  <!-- ctx:rule id="CCW-006" -->

### Accepted baseline

- **Close the post-merge baseline checkpoint before new development:** After a reviewed change is successfully merged into the accepted branch, reconcile the durable repository state that records the accepted baseline before starting the next coherent development block. Record the merge outcome in `PLAN.md`, update `STATE.md` or equivalent current-state documentation, and refresh README/CHANGELOG or review-status wording made stale by the merge when applicable.
  Why: The merge itself creates project facts after the merge candidate was frozen. Without a post-merge checkpoint, the accepted code can be correct while recovery documentation still describes the pre-merge state.
  <!-- ctx:rule id="CCW-008" -->

## Topics

### Executing a development block

When planning, resuming, checkpointing, reviewing, testing, finalizing, merging, or closing the accepted baseline for a coherent development block:

Required:
- Resource: `docs/change-workflow.md`
<!-- ctx:topic id="CCW-TOPIC-CHANGE-WORKFLOW" -->
