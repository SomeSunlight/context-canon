# ContextCanon Development Workflow — Local Context Source
<!-- ctx:node id="c4c94726-3cc7-4df6-b779-72bbf9c06f40" version="0.1.0-draft" -->

## Overview

Internal self-hosted context for carrying ContextCanon development safely across long LLM-assisted sessions, tool failures, and human review rounds. It is internal first; promote it to the reusable Node Library only after real cross-project use proves the method generic.

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

- **Resume recent explicit continuation without re-proving unchanged state:** When the project owner resumes work after a short conversational interruption, explicitly says to continue, and reports no intervening repository changes, continue from the last established branch/PR state unless a repository operation gives evidence that it changed. Do not spend a new work cycle re-checking already established repository facts merely to prove that nothing happened.
  Why: In the current single-developer workflow, repeated defensive re-verification consumes the useful working window without adding evidence. Any stated or observed intervening change still invalidates this assumption.
  <!-- ctx:rule id="CCW-007" -->

### Proportional verification

- **Batch related edits before generated-package regeneration:** For one coherent correction block, make the related authoring/code changes and run proportionate deterministic tests first; do not regenerate ContextCanon's compiler-owned self-hosted package output after every micro-edit.
  Why: Generated-output verification is valuable, but repeating the full materialization cycle after every tiny edit adds ceremony without increasing confidence in superseded intermediate heads.
  <!-- ctx:rule id="CCW-004" -->

- **Require exact-head green verification at the merge gate, not the first review gate:** A coherent development block may be presented for project-owner review while known CI failures or generated drift remain, provided that state is understood and disclosed. After explicit project-owner approval and before merging to `main`, require the exact current head to pass the deterministic test suite and `contextcanon check --all .` with zero generated drift.
  Why: Human review should happen before spending finalization effort on a candidate that may still change, while `main` remains protected by a strict reproducibility gate.
  <!-- ctx:rule id="CCW-005" -->

### Human review gate

- **Do not merge without explicit project-owner approval:** Keep a review PR open until the project owner explicitly approves the reviewed result.
  Why: Green CI proves deterministic consistency, not that the product or documentation is acceptable to its human reviewer.
  <!-- ctx:rule id="CCW-006" -->

### Accepted baseline

- **Close the post-merge baseline checkpoint before new development:** After a reviewed PR is successfully merged to `main`, reconcile the durable repository state that records the accepted baseline before starting the next coherent development block. Record the merge outcome in `PLAN.md`, update `STATE.md` and any README/CHANGELOG status text made stale by the merge, and correct live-status wording in the merged PR description when needed.
  Why: The merge itself changes project truth after the merge candidate was frozen. Without an explicit post-merge checkpoint, `main` can be mechanically correct while its recovery documentation still describes the pre-merge state.
  <!-- ctx:rule id="CCW-008" -->

## Topics

### Executing a development block

When planning, resuming, checkpointing, testing, regenerating self-hosted Context packages, or preparing a ContextCanon change block for project-owner review:

Required:
- Resource: `docs/change-workflow.md`
<!-- ctx:topic id="CCW-TOPIC-CHANGE-WORKFLOW" -->
