# ContextCanon Development Workflow

This is an **internal Context Node** for the way ContextCanon itself is developed with long-running LLM assistance and explicit project-owner review.

Start with [`CONTEXT.md`](CONTEXT.md). Edit [`CONTEXT.src.md`](CONTEXT.src.md) when the durable workflow rules change.

The Node is deliberately internal rather than immediately reusable. We first want to prove the method on ContextCanon itself. If the same workflow later works well across unrelated projects, it can be reviewed and promoted into `nodes/library/` as a reusable Node with its own versioned lifecycle.

The deeper change cadence is documented in [`docs/change-workflow.md`](docs/change-workflow.md).
