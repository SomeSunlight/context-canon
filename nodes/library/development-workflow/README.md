# Development Workflow

This is a **reusable Context Node** for recoverable, review-gated project development across long human/LLM-assisted sessions.

It defines the shared **Issue → branch → Pull Request/review → checks → merge → accepted-baseline** workflow contract. The vocabulary is deliberately familiar and concrete; this Node does not invent a second abstract process language.

The Node itself does **not** choose the development infrastructure that implements those concepts. Concrete reusable provider Nodes can compose this workflow and make the terms operational for a project, for example:

- [GitHub](../github/) — ordinary GitHub Issues, Pull Requests, reviews, checks and merge state.
- [GitHub Local](../github-local/) — a local GitHub-compatible surface for restricted-network or private development.

A project may still compose Development Workflow directly when its implementation is already unambiguous or deliberately project-specific.

Start here:

- [`CONTEXT.src.md`](CONTEXT.src.md) — durable workflow Rules and Topic entry point.
- [`docs/README.md`](docs/README.md) — orientation for the authored workflow documentation.
- [`docs/change-workflow.md`](docs/change-workflow.md) — the practical sequence from PLAN checkpoint through owner review, final verification, merge, and accepted-baseline closure.

The key boundaries are **review-ready, merge-ready, and baseline-closed**. A coherent candidate can be reviewed before all expensive finalization work is complete when remaining failures or drift are understood and disclosed; the exact intended merge head must pass the project's complete merge gate after approval; the successful merge is followed by a small durable state reconciliation before the next coherent block begins.

This Node intentionally has **no Foundation Source**. Consumers that want ContextCanon Foundation compose it separately. That keeps this workflow reusable without making an unrelated baseline an accidental transitive dependency.
