# ContextCanon Development Workflow — Official Context

> [!CAUTION]
> **GENERATED FILE — DO NOT EDIT.**
> This is the compact official entry for this Context Node.
> Together with `CONTEXT/` it forms the human/agent-facing Official Context Package.
>
> Edit [CONTEXT.src.md](CONTEXT.src.md) instead.

**Node:** ContextCanon Development Workflow  
**Context version:** `0.1.0-draft`

## Overview

Internal self-hosted context for carrying ContextCanon development safely across long LLM-assisted sessions, tool failures, and human review rounds. It is internal first; promote it to the reusable Node Library only after real cross-project use proves the method generic.

## How to use this context

Apply all Rules below to every task in this Node.

For the current task, evaluate each Topic condition. When one matches, read every **Required** target before continuing; read **Optional** targets only when useful.

## Rules

### Recoverable planning

#### `CCW-001` — Plan a coherent change block before editing

Before starting a new coherent ContextCanon development block, add a short purpose and checklist to `PLAN.md`.

#### `CCW-002` — Checkpoint completed plan items immediately

When a listed step is actually complete, mark its `PLAN.md` checkbox `[x]` immediately rather than reconstructing completion at the end of a long session.

#### `CCW-003` — Keep recovery-critical knowledge in the repository

Put decisions, active constraints, accepted state, and next steps needed to resume work in repository documentation rather than relying on chat history or model memory.

#### `CCW-007` — Resume recent explicit continuation without re-proving unchanged state

When the project owner resumes work after a short conversational interruption, explicitly says to continue, and reports no intervening repository changes, continue from the last established branch/PR state unless a repository operation gives evidence that it changed. Do not spend a new work cycle re-checking already established repository facts merely to prove that nothing happened.

### Proportional verification

#### `CCW-004` — Batch related edits before generated-package regeneration

For one coherent correction block, make the related authoring/code changes and run proportionate deterministic tests first; do not regenerate ContextCanon's compiler-owned self-hosted package output after every micro-edit.

#### `CCW-005` — Require exact-head green verification at the merge gate, not the first review gate

A coherent development block may be presented for project-owner review while known CI failures or generated drift remain, provided that state is understood and disclosed. After explicit project-owner approval and before merging to `main`, require the exact current head to pass the deterministic test suite and `contextcanon check --all .` with zero generated drift.

### Human review gate

#### `CCW-006` — Do not merge without explicit project-owner approval

Keep a review PR open until the project owner explicitly approves the reviewed result.

## Topics

### Executing a development block

When planning, resuming, checkpointing, testing, regenerating self-hosted Context packages, or preparing a ContextCanon change block for project-owner review:

**Required**

- [`CONTEXT/references/nodes/internal/development-workflow/docs/change-workflow.md`](CONTEXT/references/nodes/internal/development-workflow/docs/change-workflow.md)
