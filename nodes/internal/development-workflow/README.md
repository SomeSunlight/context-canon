# ContextCanon Development Workflow

This is an **internal self-hosted Context Node** for how ContextCanon itself is developed across long LLM-assisted sessions and project-owner review rounds.

It exists so the working method is durable repository context rather than an unwritten chat convention.

Start here:

- [`CONTEXT.src.md`](CONTEXT.src.md) — durable workflow Rules and the Topic entry point.
- [`docs/README.md`](docs/README.md) — orientation for the authored workflow documentation.
- [`docs/change-workflow.md`](docs/change-workflow.md) — the practical sequence from PLAN checkpoint through project-owner review, the final merge gate, and accepted-baseline closure after merge.

The key boundaries are **review-ready, merge-ready, and baseline-closed**: the project owner may review a coherent large-line candidate while understood CI drift remains; exact-head full green CI and zero generated drift are required only after approval, before merge to `main`; after the successful merge, durable repository status is reconciled before a new coherent development block begins.

This Node is intentionally under `nodes/internal/`. If repeated use in unrelated projects proves the workflow genuinely reusable, promote it through an explicit reviewed library contribution rather than assuming that now.
