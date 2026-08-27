# ContextCanon Foundation

This directory is the node root for **ContextCanon Foundation**, the common reusable baseline shipped in the ContextCanon Node Library.

Start with [`CONTEXT.md`](CONTEXT.md) to see the compiled Rules and Topic navigation. Edit [`CONTEXT.src.md`](CONTEXT.src.md) when changing Foundation itself.

## What is authored here

- [`CONTEXT.src.md`](CONTEXT.src.md) — the reusable Foundation Rules and Topic map.
- [`docs/`](docs/) — human-authored reusable guidance for ContextCanon authoring, official packages, Topics, composition, and harness adapters.

`CONTEXT.md`, `CONTEXT/`, and `.context/` are generated compiler/package state. In particular, files under `CONTEXT/references/` are materialized copies of authored documentation referenced by Foundation Topics; they are not another authoring surface.

Foundation intentionally contains reusable ContextCanon guidance. Repository-internal implementation and development method belong under [`../../internal/`](../../internal/) instead.
