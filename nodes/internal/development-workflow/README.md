# ContextCanon Development Workflow

This is an **internal dogfood Context Node** for how ContextCanon itself is developed across long LLM-assisted sessions and project-owner review rounds.

It exists so the working method is durable repository context rather than an unwritten chat convention.

Start here:

- [`CONTEXT.src.md`](CONTEXT.src.md) — durable workflow Rules and the Topic entry point.
- [`docs/README.md`](docs/README.md) — orientation for the authored workflow documentation.
- [`docs/change-workflow.md`](docs/change-workflow.md) — the practical sequence from PLAN checkpoint through project-owner review to the final merge gate.

The key distinction is **review-ready versus merge-ready**: the project owner may review a coherent large-line candidate while understood CI drift remains; exact-head full green CI and zero generated drift are required only after approval, before merge to `main`.

This Node is intentionally under `nodes/internal/`. If repeated use in unrelated projects proves the workflow genuinely reusable, promote it through an explicit reviewed library contribution rather than assuming that now.
