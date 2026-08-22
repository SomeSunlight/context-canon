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

## Local Rules

### Compiler architecture

#### `CCI-001` — Deterministic skeleton, semantic intelligence on top

Prefer deterministic mechanisms whenever behavior can be specified and computed exactly; use LLMs only for work that genuinely requires semantic interpretation.

#### `CCI-005` — Keep compiler stages separated

Keep the compiler pipeline explicit: `parser.py` parses authoring syntax into `model.py` structures; `compiler.py` resolves and composes semantics; `render.py` produces deterministic text; `outputs.py` compares or writes generated files; `cli.py` only orchestrates commands.

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

When changing, debugging, reviewing, or extending the deterministic compiler implementation, parser grammar, semantic composition, rendering, generated-output handling, CLI, or compiler tests:

**Required**

- [`CONTEXT/references/docs/compiler.md`](CONTEXT/references/docs/compiler.md)

### Framework architecture

When changing the compiler boundary, package model, Node structure, deterministic/semantic split, or generated artifacts:

**Required**

- [`CONTEXT/references/docs/architecture.md`](CONTEXT/references/docs/architecture.md)
- [`CONTEXT/references/docs/use-case-walkthrough.md`](CONTEXT/references/docs/use-case-walkthrough.md)

**Optional**

- [`CONTEXT/references/docs/concepts.md`](CONTEXT/references/docs/concepts.md)

### Source and official formats

When changing authoring syntax, IDs, Topics, Changes, official entry views, or machine representation:

**Required**

- [`CONTEXT/references/docs/source-format.md`](CONTEXT/references/docs/source-format.md)
- [`CONTEXT/references/docs/official-context.md`](CONTEXT/references/docs/official-context.md)
- [`CONTEXT/references/docs/topics.md`](CONTEXT/references/docs/topics.md)

### Composition

When changing Source composition, version acceptance, conflicts, removes, overrides, exceptions, or multi-Node repositories:

**Required**

- [`CONTEXT/references/docs/composition.md`](CONTEXT/references/docs/composition.md)
- [`CONTEXT/references/docs/use-case-walkthrough.md`](CONTEXT/references/docs/use-case-walkthrough.md)

### Harness integration

When changing `AGENTS.md`, `.goosehints`, or another model/harness adapter:

**Required**

- [`CONTEXT/references/docs/harnesses.md`](CONTEXT/references/docs/harnesses.md)

### State and planning

When deciding whether information belongs in current state, planning, governance, or history:

**Required**

- [`CONTEXT/references/docs/state.md`](CONTEXT/references/docs/state.md)
