# ContextCanon Foundation documentation

These are the **human-authored reusable documents owned by ContextCanon Foundation**.

Start with the Node's [`CONTEXT.md`](../CONTEXT.md) rather than reading this directory as a preload list. Foundation Topics select the documents needed for context authoring, composition, and harness integration.

## What belongs here

- [`source-format.md`](source-format.md) — reusable `CONTEXT.src.md` authoring syntax and identity rules.
- [`official-context.md`](official-context.md) — the compiled Official Context Package and generated package boundary.
- [`topics.md`](topics.md) — progressive-disclosure Topic semantics and resource materialization.
- [`composition.md`](composition.md) — Source composition, local changes, exact accepted packages, and update semantics.
- [`harnesses.md`](harnesses.md) — harness-neutral adapter principles and current compatibility guidance.

Framework-implementation architecture, compiler internals, onboarding implementation, tests/CI, project state, and ContextCanon's own development history belong to the internal [Framework Development Node](../../internal/framework-development/) instead.

## Authoring versus generated package copies

Files in this directory are authored source documentation. During compilation, Topic resources are materialized into generated `CONTEXT/references/...` package paths so Foundation can be published and consumed independently of this repository.

Only the files under `docs/` are edited. Generated files under `CONTEXT/` and `.context/` are compiler/package output and must not be maintained separately.
