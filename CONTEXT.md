# ContextCanon Development — Official Context

> [!CAUTION]
> **GENERATED FILE — DO NOT EDIT.**
> This is the compact official entry view for developing ContextCanon itself.
> The complete Official Context is the compiled package represented by this entry view plus Topic material and machine package data.
>
> Edit [CONTEXT.src.md](CONTEXT.src.md) instead.
> Client projects should compose [ContextCanon Standard](contexts/standard/CONTEXT.md), not this Development node.

**Node:** ContextCanon Development  
**Context version:** `0.1.0-draft`

Published rule IDs are stable contract identifiers. Titles and wording may change without changing identity.

## Rules from ContextCanon Standard

### Canonical context

#### `CC-001` — One official package

The compiled Official Context Package is the single canonical context for a node: it applies to the node itself and is the package meaning published to child nodes.

#### `CC-002` — Edit source, not generated views

Human context changes are authored in `CONTEXT.src.md`; generated context views, machine state, and harness adapters are not edited directly.

### Machine state

#### `CC-003` — Keep compiler bookkeeping out of the normal workflow

Framework bookkeeping belongs under `.context/` and should not be required reading for normal human or agent work.

### Composition

#### `CC-004` — No implicit source precedence

Context sources are composed without implicit precedence; conflicts are resolved explicitly through local changes rather than source order.

### Identity

#### `CC-005` — Stable identity

Every addressable context element has a stable ID independent of its title, wording, file location, and presentation.

#### `CC-006` — Publish IDs that children may reference

Published official contexts expose stable IDs for rules and other elements that child nodes may reference.

### Progressive disclosure

#### `CC-007` — Keep entry context small

Keep the official entry context compact and use Topics to load deeper context only when needed; Topic references distinguish required from optional material.

### Project state

#### `CC-008` — State stays local

`STATE.md` describes the current local project situation and is never inherited as governance by child nodes.

### Harness independence

#### `CC-009` — Canonical context is model- and harness-neutral

Project code and canonical project context must not depend on a particular LLM or agent harness; harness-specific files are thin generated adapters at the edge.

### Repository conventions

#### `CC-010` — Keep standard repository documents explicit

Keep `README.md`, `CONTRIBUTING.md`, and `CHANGELOG.md` present even when one is intentionally short.

## Local Development rules

### Compiler architecture

#### `CCI-001` — Deterministic skeleton, semantic intelligence on top

Prefer deterministic mechanisms whenever behavior can be specified and computed exactly; use LLMs only for work that genuinely requires semantic interpretation.

Why: Deterministic structure provides reproducibility and auditability, while LLM reasoning is most valuable where meaning rather than mechanics must be understood.

### Development method

#### `CCI-002` — Validate vertically before hardening

Validate ContextCanon through concrete repository use cases before hardening abstractions into compiler code.

Why: Simple real workflows should shape the framework; implementation convenience must not force unnecessary ceremony on users.

#### `CCI-003` — Repository documentation is the design record

Treat the repository documentation as the canonical design record once a decision is accepted; do not rely on reconstructing architecture from chat history.

Why: ContextCanon itself should demonstrate durable, reviewable project context.

## Topics

### Framework architecture

When changing the compiler boundary, package model, node structure, deterministic/semantic split, or generated artifacts:

**Required**
- `docs/architecture.md`
- `docs/use-case-walkthrough.md`

**Optional**
- `docs/concepts.md`

### Source and official formats

When changing authoring syntax, IDs, Topics, official entry views, or machine representation:

**Required**
- `docs/source-format.md`
- `docs/official-context.md`
- `docs/topics.md`

### Composition

When changing source composition, version acceptance, conflicts, removes, overrides, exceptions, or multi-node repositories:

**Required**
- `docs/composition.md`
- `docs/use-case-walkthrough.md`

### Harness integration

When changing `AGENTS.md`, `.goosehints`, or another model/harness adapter:

**Required**
- `docs/harnesses.md`

### State and planning

When deciding whether information belongs in current state, planning, governance, or history:

**Required**
- `docs/state.md`
