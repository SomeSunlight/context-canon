# ContextCanon Development Workflow

This is an **internal Context Node** for the way ContextCanon itself is developed with long-running LLM assistance and explicit project-owner review.

[`CONTEXT.src.md`](CONTEXT.src.md) is the authored source. A normal ContextCanon build generates `CONTEXT.md`, which then becomes the compact Official Context entry for this Node.

The Node is deliberately internal rather than immediately reusable. We first want to prove the method on ContextCanon itself. If the same workflow later works well across unrelated projects, it can be reviewed and promoted into `nodes/library/` as a reusable Node with its own versioned lifecycle.

The deeper change cadence is documented in [`docs/change-workflow.md`](docs/change-workflow.md).
