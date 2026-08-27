# ContextCanon Framework Development — Official Context

> [!CAUTION]
> **GENERATED FILE — DO NOT EDIT.**
> This is the compact official entry for this Context Node.
> Together with `CONTEXT/` it forms the human/agent-facing Official Context Package.
>
> Edit [CONTEXT.src.md](CONTEXT.src.md) instead.

**Node:** ContextCanon Framework Development  
**Context version:** `0.1.0-draft`

## How to use this context

Apply all Rules below to every task in this Node.

For the current task, evaluate each Topic condition. When one matches, read every **Required** target before continuing; read **Optional** targets only when useful.

## Rules from ContextCanon Foundation

### Canonical context

#### `CC-001` — One official package

The compiled Official Context Package is the single canonical context for a Node: it applies to the Node itself and is the package meaning published to child Nodes.

#### `CC-002` — Edit source, not generated output

Human context changes are authored in `CONTEXT.src.md`; generated context views, package contents, machine state, and harness adapters are not edited directly.

### Machine state

#### `CC-003` — Keep compiler bookkeeping out of the normal workflow

Framework bookkeeping belongs under `.context/` and should not be required reading for normal human or agent work.

### Composition

#### `CC-004` — No implicit Source precedence

Context Sources are composed without implicit precedence; conflicts are resolved explicitly through local changes rather than Source order.

### Identity

#### `CC-005` — Stable identity

Every addressable context element has a stable ID independent of its title, wording, file location, and presentation.

#### `CC-006` — Publish IDs that children may reference

Published official contexts expose stable IDs for Rules and other elements that child Nodes may reference.

### Progressive disclosure

#### `CC-007` — Keep entry context small

Keep the official entry context compact and use Topics to load deeper context only when needed; Topic targets distinguish Required from Optional material.

### Project state

#### `CC-008` — State stays local

`STATE.md` describes the current local project situation and is never inherited as governance by child Nodes.

### Harness independence

#### `CC-009` — Canonical context is model- and harness-neutral

Project code and canonical project context must not depend on a particular LLM or agent harness; harness-specific files are thin generated adapters at the edge.

### Repository conventions

#### `CC-010` — Keep familiar repository documents useful

Keep `README.md`, `CONTRIBUTING.md`, and `CHANGELOG.md` present when they are useful to the repository even when ContextCanon is present.

### Documentation style

#### `CC-011` — Write for intelligent readers

Write technical documentation in precise, plain prose for intelligent readers; introduce unfamiliar concepts before using specialized terms and avoid unexplained internal shorthand, inflated marketing language, and unnecessary jargon.

## Rules from ContextCanon Development Workflow

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

## Local Rules

### Compiler architecture

#### `CCI-001` — Deterministic skeleton, semantic intelligence on top

Prefer deterministic mechanisms whenever behavior can be specified and computed exactly; use LLMs only for work that genuinely requires semantic interpretation.

#### `CCI-005` — Keep compiler stages separated

Keep the compiler pipeline explicit: `parser.py` parses authoring syntax into `model.py` structures; `compiler.py` resolves and composes semantics; `render.py` produces deterministic text; `outputs.py` compares or writes generated files; `cli.py` only orchestrates commands.

### Onboarding trust

#### `CCI-006` — Keep new Node identity independent from Evidence identity

A newly onboarded Context Node must receive human-owned stable identity; when ContextCanon generates that identity it creates a fresh UUID once and stores it in review state rather than deriving it from the Evidence digest.

#### `CCI-007` — Bind reusable Sources to the exact reviewed package

An onboarding proposal that reuses an existing Source must bind the Source Node ID, name, version, normalized digest, and package digest inspected by the semantic reviewer, and final acceptance must require that same immutable package.

#### `CCI-008` — Do not seize project-owned paths during first adoption

Before first onboarding publication, compile the proposed Node in staging, derive its actual compiler-owned output paths, and refuse publication when those outputs or canonical Context authoring/resource paths are already owned by the project.

#### `CCI-009` — Make first-adoption publication rollback-safe

Treat first onboarding publication as one transaction-like state change; if publication fails before the acceptance record is complete, remove only the canonical/generated state and Source packages newly created by that failed attempt while preserving pre-existing accepted state.

### Development method

#### `CCI-002` — Validate vertically before hardening

Validate ContextCanon through concrete repository use cases before hardening abstractions into compiler code.

#### `CCI-003` — Repository documentation is the design record

Treat the repository documentation as the canonical design record once a decision is accepted; do not rely on reconstructing architecture from chat history.

### Node library

#### `CCI-004` — Keep library Nodes on Foundation

Every reusable Node published in the ContextCanon Node Library must compose ContextCanon Foundation directly or transitively.

## Topics

### Compiler implementation

When changing, debugging, reviewing, or extending the deterministic compiler implementation, parser grammar, semantic composition, rendering, generated-output handling, CLI, or compiler behavior:

**Required**

- [`CONTEXT/references/nodes/internal/framework-development/docs/compiler.md`](CONTEXT/references/nodes/internal/framework-development/docs/compiler.md)

### Tests and CI

When changing or reviewing tests, GitHub Actions, repository consistency checks, self-hosted generated-package drift verification, or when diagnosing why a pull-request check failed, first understand the two test levels: deterministic behavior tests and exact generated-output drift checking.

**Required**

- [`CONTEXT/references/nodes/internal/framework-development/docs/tests-and-ci.md`](CONTEXT/references/nodes/internal/framework-development/docs/tests-and-ci.md)

### Development workflow

When planning, resuming, checkpointing, testing, regenerating ContextCanon's own generated packages, or preparing a ContextCanon development block for project-owner review:

**Required**

- [ContextCanon Development Workflow](../development-workflow/CONTEXT.md)

### Framework architecture

When changing the compiler boundary, package model, Node structure, deterministic/semantic split, or generated artifacts:

**Required**

- [`CONTEXT/references/nodes/internal/framework-development/docs/architecture.md`](CONTEXT/references/nodes/internal/framework-development/docs/architecture.md)
- [`CONTEXT/references/nodes/internal/framework-development/docs/use-case-walkthrough.md`](CONTEXT/references/nodes/internal/framework-development/docs/use-case-walkthrough.md)

**Optional**

- [`CONTEXT/references/nodes/internal/framework-development/docs/concepts.md`](CONTEXT/references/nodes/internal/framework-development/docs/concepts.md)

### Reviewed project onboarding

When changing onboarding inventory, evidence capture, semantic classification, proposal review/acceptance, or extraction of reusable context from an existing project:

**Required**

- [`CONTEXT/references/nodes/internal/framework-development/docs/onboarding-reference.md`](CONTEXT/references/nodes/internal/framework-development/docs/onboarding-reference.md)

### Source and official formats

When changing authoring syntax, IDs, Topics, Changes, official entry views, or machine representation:

**Required**

- [`CONTEXT/references/nodes/library/foundation/docs/source-format.md`](CONTEXT/references/nodes/library/foundation/docs/source-format.md)
- [`CONTEXT/references/nodes/library/foundation/docs/official-context.md`](CONTEXT/references/nodes/library/foundation/docs/official-context.md)
- [`CONTEXT/references/nodes/library/foundation/docs/topics.md`](CONTEXT/references/nodes/library/foundation/docs/topics.md)

### Composition

When changing Source composition, version acceptance, conflicts, removes, overrides, exceptions, or multi-Node repositories:

**Required**

- [`CONTEXT/references/nodes/library/foundation/docs/composition.md`](CONTEXT/references/nodes/library/foundation/docs/composition.md)
- [`CONTEXT/references/nodes/internal/framework-development/docs/use-case-walkthrough.md`](CONTEXT/references/nodes/internal/framework-development/docs/use-case-walkthrough.md)

### Harness integration

When changing `AGENTS.md`, `.goosehints`, or another model/harness adapter:

**Required**

- [`CONTEXT/references/nodes/library/foundation/docs/harnesses.md`](CONTEXT/references/nodes/library/foundation/docs/harnesses.md)

### State and planning

When deciding whether information belongs in current state, planning, governance, or history:

**Required**

- [`CONTEXT/references/nodes/internal/framework-development/docs/state.md`](CONTEXT/references/nodes/internal/framework-development/docs/state.md)
