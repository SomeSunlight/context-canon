# Development Workflow

This is a **reusable Context Node** for recoverable, review-gated project development across long human/LLM-assisted sessions.

It exists so a proven working method can be reused across repositories without copying the same planning, review, merge-gate, and post-merge rules into every project.

Start here:

- [`CONTEXT.src.md`](CONTEXT.src.md) — durable workflow Rules and Topic entry point.
- [`docs/README.md`](docs/README.md) — orientation for the authored workflow documentation.
- [`docs/change-workflow.md`](docs/change-workflow.md) — the practical sequence from PLAN checkpoint through owner review, final verification, merge, and accepted-baseline closure.

The key boundaries are **review-ready, merge-ready, and baseline-closed**. A coherent candidate can be reviewed before all expensive finalization work is complete when remaining failures or drift are understood and disclosed; the exact intended merge head must pass the project's complete merge gate after approval; the successful merge is followed by a small durable state reconciliation before the next coherent block begins.

This Node intentionally has **no Foundation Source**. Consumers that want ContextCanon Foundation compose it separately. That keeps this workflow reusable without making an unrelated baseline an accidental transitive dependency.
